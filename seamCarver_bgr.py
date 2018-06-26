import cv2
import numpy as np

INF = 1000000

class SeamCarver:
    def __init__(self, image):
        print('seamCarver bgr')
        self.kernel_x = np.array([[0.,0.,0.], [-1.,0.,1.], [0.,0.,0.]], dtype=np.float32)
        self.kernel_y_left = np.array([[0.,0.,0.], [0.,0.,1.], [0.,-1.,0.]], dtype=np.float32)
        self.kernel_y_right = np.array([[0.,0.,0.], [1.,0.,0.], [0.,-1.,0.]], dtype=np.float32)
        self.constant = 1000

        self.image = image
        self.original_image = image
        self.image_height, self.image_width = image.shape[:2]
        self.original_height, self.original_width = image.shape[:2]

        self.seams_index = [[], []]
        self.original_seams = [[], []]

    def clear_seams(self):
        self.seams_index = [[], []]
        self.original_seams = [[], []]

    def refresh(self):
        self.image = self.original_image[:]
        self.image_height, self.image_width = self.original_image.shape[:2]
        self.seams_index[0] = self.original_seams[0].copy()
        self.seams_index[1] = self.original_seams[1].copy()
        if self.original_delta is not None:
            self.delta = self.original_delta

    def resize_aim(self, output_height, output_width):
        self.output_height = output_height
        self.output_width = output_width
        self.original_delta = None

    def protect_resize_aim(self, output_height, output_width, protect_mask):
        self.mask_image = protect_mask
        self.output_width = output_width
        self.output_height = output_height
        self.mask_height, self.mask_width = protect_mask.shape[:2]
        self.object_height, self.object_width = self.get_mask_size()

    def remove_aim(self, mask_image):
        self.mask_image = mask_image
        self.mask_height, self.mask_width = mask_image.shape[:2]
        self.object_height, self.object_width = self.get_mask_size()

    def realtime_resize(self, output_height, output_width, protect=False):
        delta_row, delta_col = output_height - self.image_height, output_width - self.image_width
        if delta_col > 0:
            self.seam_insert(delta_col, direction=0, protect=protect)
        if delta_row > 0:
            self.rotate_image(2)
            self.seam_insert(delta_row, direction=1, protect=protect)
            self.rotate_image(0)
        if delta_col < 0:
            self.seam_remove(abs(delta_col), direction=0, protect=protect)
        if delta_row < 0:
            self.rotate_image(2)
            self.seam_remove(abs(delta_row), direction=1, protect=protect)
            self.rotate_image(0)
        return self.image

    def get_resize_seams(self, protect=False):
        delta_row, delta_col = self.output_height - self.image_height, self.output_width - self.image_width
        temp_img = self.image
        if delta_col > 0:
            self.seam_insert(delta_col, direction=0, protect=protect)
        if delta_row > 0:
            self.rotate_image(2)
            if protect:
                self.rotate_mask_image(2)
            self.seam_insert(delta_row, direction=1, protect=protect)
            if protect:
                self.rotate_mask_image(0)
            self.rotate_image(0)
        if delta_col < 0:
            self.seam_remove(abs(delta_col), direction=0, protect=protect)
        if delta_row < 0:
            self.rotate_image(2)
            if protect:
                self.rotate_mask_image(2)
            self.seam_remove(abs(delta_row), direction=1, protect=protect)
            if protect:
                self.rotate_mask_image(0)
            self.rotate_image(0)
        self.image = temp_img
        self.image_height, self.image_width = self.image.shape[:2]
        self.original_seams[0] = self.seams_index[0].copy()
        self.original_seams[1] = self.seams_index[1].copy()

    def get_removal_seams(self):
        temp_img = self.image

        direction = 0
        if self.object_height < self.object_width:
            self.rotate_image(2)
            self.rotate_mask_image(2)
            direction = 1

        while len(np.where(self.mask_image > 0)[0]) > 0:
            energy_map = self.calc_energy_map().astype(np.float32)
            energy_map[self.mask_image > 0] *= -self.constant
            cumulative_map = self.cumulative_map(energy_map, 0)
            seam = self.find_seam(cumulative_map)
            self.seams_index[direction].append(seam)
            self.delete_seam(seam)
            self.delete_mask_seam(seam)

        self.delta = len(self.seams_index[direction])
        self.original_delta = self.delta

        self.seam_insert(self.delta, direction, start=self.delta)
        self.image = temp_img
        self.image_height, self.image_width = self.image.shape[:2]
        if direction == 1:
            self.rotate_mask_image(2)
        self.original_seams[0] = self.seams_index[0].copy()
        self.original_seams[1] = self.seams_index[1].copy()

    def seam_remove(self, delta, direction, protect=False):
        for i in range(delta):
            energy_map = self.calc_energy_map().astype(np.float32)
            if protect:
                energy_map[self.mask_image > 0] *= self.constant
            cumulative_map = self.cumulative_map(energy_map, 0)
            seam = self.find_seam(cumulative_map)
            self.seams_index[direction].append(seam)
            self.delete_seam(seam)
            if protect:
                self.delete_mask_seam(seam)

    def seam_insert(self, delta, direction, protect=False, start=0):
        temp_img = np.copy(self.image)

        for i in range(delta):
            energy_map = self.calc_energy_map().astype(np.float32)
            if protect:
                energy_map[self.mask_image > 0] *= self.constant
            cumulative_map = self.cumulative_map(energy_map, 1)
            seam = self.find_seam(cumulative_map)
            self.seams_index[direction].append(seam)
            self.delete_seam(seam)

        self.image = temp_img
        self.image_width = self.image.shape[1]

        for i in range(start, start+delta):
            seam = self.seams_index[direction][i]
            self.add_seam(seam)
            if protect:
                self.add_mask_seam(seam)
            self.seams_index[direction][i+1:] = self.update_seams(self.seams_index[direction][i+1:], seam)

    def calc_energy_map(self):
        b, g, r = cv2.split(self.image)
        b_energy = np.absolute(cv2.Scharr(b, -1, 1, 0)) + np.absolute(cv2.Scharr(b, -1, 0, 1))
        g_energy = np.absolute(cv2.Scharr(g, -1, 1, 0)) + np.absolute(cv2.Scharr(g, -1, 0, 1))
        r_energy = np.absolute(cv2.Scharr(r, -1, 1, 0)) + np.absolute(cv2.Scharr(r, -1, 0, 1))
        return b_energy + g_energy + r_energy

    def cumulative_map(self, energy_map, direction):
        r, c = energy_map.shape
        retmap = energy_map.astype(np.float32)
        if direction == 0:
            dx_map = self.calc_neighbours(self.kernel_x)
            dly_map = self.calc_neighbours(self.kernel_y_left)
            dry_map = self.calc_neighbours(self.kernel_y_right)

            for row in range(1, r):
                for col in range(c):
                    e_up = retmap[row-1, col] + dx_map[row-1, col]
                    e_right = retmap[row-1, col+1] + dx_map[row-1, col+1] + dry_map[row-1, col+1] if col < c-1 else INF
                    e_left = retmap[row-1, col-1] + dx_map[row-1, col-1] + dly_map[row-1, col-1] if col > 0 else INF
                    retmap[row, col] = energy_map[row, col] + min(e_left, e_right, e_up)

        else:
            for row in range(1, r):
                for col in range(c):
                    retmap[row, col] = energy_map[row, col] + np.min(retmap[row-1, max(col-1, 0) : min(col+2, c-1)])

        return retmap

    def calc_neighbours(self, kernel):
        b, g, r = cv2.split(self.image)
        ret = np.absolute(cv2.filter2D(b, -1, kernel=kernel)) + \
              np.absolute(cv2.filter2D(g, -1, kernel=kernel)) + \
              np.absolute(cv2.filter2D(r, -1, kernel=kernel))
        return ret

    def showing_process(self, mode='resize'):
        def insertion_process(direction):
            seam = self.seams_index[direction].pop(0)
            self.add_seam(seam)
            self.show_seam(seam, direction)

        def deletion_process(direction):
            seam = self.seams_index[direction].pop(0)
            self.show_seam(seam, direction)
            self.delete_seam(seam)

        if mode == 'resize':
            delta_row, delta_col = self.output_height - self.image_height, self.output_width - self.image_width

            if delta_col > 0:
                insertion_process(direction=0)
                return cv2.cvtColor(self.show_image, cv2.COLOR_BGR2RGB), True

            if delta_row > 0:
                self.rotate_image(2)
                insertion_process(direction=1)
                self.rotate_image(0)
                return cv2.cvtColor(self.show_image, cv2.COLOR_BGR2RGB), True

            if delta_col < 0:
                deletion_process(direction=0)
                return cv2.cvtColor(self.show_image, cv2.COLOR_BGR2RGB), True

            if delta_row < 0:
                self.rotate_image(2)
                deletion_process(direction=1)
                self.rotate_image(0)
                return cv2.cvtColor(self.show_image, cv2.COLOR_BGR2RGB), True

            output_image = cv2.cvtColor(self.image.astype(np.uint8), cv2.COLOR_BGR2RGB)
            return output_image, False
        else:
            direction = 0
            if self.object_height < self.object_width:
                self.rotate_image(2)
                self.rotate_mask_image(2)
                direction = 1

            if self.delta > 0:
                deletion_process(direction)
                self.delta -= 1
                if direction == 1:
                    self.rotate_image(0)
                    self.rotate_mask_image(0)
                return cv2.cvtColor(self.show_image, cv2.COLOR_BGR2RGB), True
            elif len(self.seams_index[direction]) > 0:
                insertion_process(direction)
                if direction == 1:
                    self.rotate_image(0)
                    self.rotate_mask_image(0)
                return cv2.cvtColor(self.show_image, cv2.COLOR_BGR2RGB), True
            else:
                if direction == 1:
                    self.rotate_image(0)
                    self.rotate_mask_image(0)
                output_image = cv2.cvtColor(self.image.astype(np.uint8), cv2.COLOR_BGR2RGB)
                return output_image, False

    def find_seam(self, cumulative_map):
        r, c = cumulative_map.shape
        retseam = np.zeros((r, ), dtype=np.uint32)
        retseam[-1] = np.argmin(cumulative_map[-1])
        for row in range(r-2, -1, -1):
            pre_x = retseam[row+1]
            if pre_x == 0:
                retseam[row] = np.argmin(cumulative_map[row, :2])
            else:
                retseam[row] = np.argmin(cumulative_map[row, pre_x-1:min(pre_x+2, c-1)]) + pre_x - 1

        return retseam

    def show_seam(self, seams, direction):
        self.show_image = np.copy(self.image)
        for row in range(self.image_height):
            col = seams[row]
            self.show_image[row, col, 0] = 0
            self.show_image[row, col, 1] = 0
            self.show_image[row, col, 2] = 255

        self.show_image = (cv2.rotate(self.show_image, 0) if direction == 1 else self.show_image).astype(np.uint8)

    def delete_seam(self, seam):
        output = np.zeros((self.image_height, self.image_width-1, 3), dtype=np.float32)
        for row in range(self.image_height):
            col = seam[row]
            output[row, :, 0] = np.delete(self.image[row, :, 0], [col])
            output[row, :, 1] = np.delete(self.image[row, :, 1], [col])
            output[row, :, 2] = np.delete(self.image[row, :, 2], [col])
        self.image = output
        self.image_width -= 1

    def delete_mask_seam(self, seam):
        output = np.zeros((self.mask_height, self.mask_width-1))
        for row in range(self.mask_height):
            col = seam[row]
            output[row, :] = np.delete(self.mask_image[row, :], [col])
        self.mask_image = output
        self.mask_width -= 1

    def add_seam(self, seam):
        temp_img = np.zeros((self.image_height, self.image_width+1, 3), dtype=np.float32)
        for row in range(self.image_height):
            col = seam[row]
            for channel in range(3):
                if col == 0:
                    temp_img[row, 0, channel] = self.image[row, 0, channel]
                    temp_img[row, 1, channel] = np.average(self.image[row, :2, channel])
                else:
                    temp_img[row, :col, channel] = self.image[row, :col, channel]
                    temp_img[row, col, channel] = np.average(self.image[row, col-1:col+1, channel])

                temp_img[row, col+1:, channel] = self.image[row, col:, channel]
        self.image = temp_img
        self.image_width += 1

    def add_mask_seam(self, seam):
        temp_img = np.zeros((self.mask_height, self.mask_width+1), dtype=np.float32)
        for row in range(self.mask_height):
            col = seam[row]
            if col == 0:
                temp_img[row, 0] = self.mask_image[row, 0]
                temp_img[row, 1] = np.average(self.image[row, :2])
            else:
                temp_img[row, :col] = self.image[row, :col]
                temp_img[row, col] = np.average(self.image[row, col - 1:col + 1])
            temp_img[row, col + 1:] = self.image[row, col:]
        self.mask_image = temp_img
        self.mask_width += 1

    def update_seams(self, remaining_seams, current_seam):
        output = []
        for seam in remaining_seams:
            seam[seam >= current_seam] += 2
            output.append(seam)
        return output

    def rotate_image(self, angle):
        self.image = cv2.rotate(self.image, angle)
        self.image_height, self.image_width = self.image_width, self.image_height

    def rotate_mask_image(self, angle):
        self.mask_image = cv2.rotate(self.mask_image, angle)
        self.mask_height, self.mask_width = self.mask_width, self.mask_height

    def get_mask_size(self):
        rows, cols = np.where(self.mask_image > 0)[:2]
        height = np.max(rows) - np.min(rows) + 1
        width = np.amax(cols) - np.min(cols) + 1
        return height, width