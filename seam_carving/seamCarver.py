import cv2
import numpy as np

class SeamCarver:
    def __init__(self, image):
        self.kernel_x = np.array([[0.,0.,0.], [-1.,0.,1.], [0.,0.,0.]], dtype=np.float64)
        self.kernel_y_left = np.array([[0.,0.,0.], [0.,0.,1.], [0.,-1.,0.]], dtype=np.float64)
        self.kernel_y_right = np.array([[0.,0.,0.], [1.,0.,0.], [0.,-1.,0.]], dtype=np.float64)
        self.constant = 1000

        self.image = image
        self.image_height, self.image_width = image.shape[:2]

    def resize(self, output_size, is_show=False):
        delta_row, delta_col = output_size[0] - self.image_height, output_size[1] - self.image_width

        if delta_col < 0:
            self.seam_remove(abs(delta_col), direction=0, is_show=is_show)
        elif delta_col > 0:
            self.seam_insert(delta_col, is_show=is_show)

        self.image = cv2.rotate(self.image, 2)
        self.image_height, self.image_width = self.image_width, self.image_height
        if delta_row < 0:
            self.seam_remove(abs(delta_row), direction=1, is_show=is_show)
        elif delta_row > 0:
            self.seam_insert(delta_row, is_show=is_show)
        self.image = cv2.rotate(self.image, 0)
        self.image_height, self.image_width = self.image_width, self.image_height

        return self.image

    def removal(self, object):
        return

    def seam_remove(self, delta, direction, is_show=False):
        for i in range(delta):
            energy_map = self.calc_energy_map()
            cumulative_map = self.cumulative_map(energy_map, 0)
            seam = self.find_seam(cumulative_map)
            if is_show:
                self.show_image = self.show_seam(seam, direction)
            self.delete_seam(seam)

    def seam_insert(self, delta, is_show=False):
        # temp_img = self.image
        # seams_record = []

        for i in range(delta):
            energy_map = self.calc_energy_map()
            cumulative_map = self.cumulative_map(energy_map, 1)
            seam = self.find_seam(cumulative_map)
            # self.add_seam(seam)
            self.seams_list.append(seam)
            self.delete_seam(seam)

        self.image = temp_img
        self.image_width = self.image.shape[1]

        for i in range(delta):
            seam = seams_record.pop()
            self.add_seam(seam)
            if is_show:
                self.show_image(seam)
            seams_record = self.update_seams(seams_record, seam)

    def calc_energy_map(self):
        b, g, r = cv2.split(self.image)
        b_energy = np.absolute(cv2.Scharr(b, -1, 1, 0)) + np.absolute(cv2.Scharr(b, -1, 0, 1))
        g_energy = np.absolute(cv2.Scharr(g, -1, 1, 0)) + np.absolute(cv2.Scharr(g, -1, 0, 1))
        r_energy = np.absolute(cv2.Scharr(r, -1, 1, 0)) + np.absolute(cv2.Scharr(r, -1, 0, 1))

        return b_energy + g_energy + r_energy

    def cumulative_map(self, energy_map, direction):
        r, c = energy_map.shape

        retmap = energy_map.astype(np.float64)
        if direction == 0:
            dx_map = self.calc_neighbours(self.kernel_x)
            dly_map = self.calc_neighbours(self.kernel_y_left)
            dry_map = self.calc_neighbours(self.kernel_y_right)

            INF = 1000000
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

    def find_seam(self, cumulative_map):
        r, c = cumulative_map.shape
        ret_seam = np.zeros((r, ), dtype=np.uint32)
        ret_seam[-1] = np.argmin(cumulative_map[-1])
        for row in range(r-2, -1, -1):
            pre_x = ret_seam[row+1]
            if pre_x == 0:
                ret_seam[row] = np.argmin(cumulative_map[row, :2])
            else:
                ret_seam[row] = np.argmin(cumulative_map[row, pre_x-1:min(pre_x+2, c-1)]) + pre_x - 1

        return ret_seam

    def show_seam(self, seam, direction):
        for row in range(self.image_height):
            col = seam[row]
            self.image[row, col, 0] = 0
            self.image[row, col, 1] = 0
            self.image[row, col, 2] = 255

        output = cv2.rotate(self.image, 0) if direction == 1 else self.image
        cv2.imshow('test', output.astype(np.uint8))
        cv2.waitKey(1)

    def delete_seam(self, seam):
        output = np.zeros((self.image_height, self.image_width-1, 3))
        for row in range(self.image_height):
            col = seam[row]
            output[row, :, 0] = np.delete(self.image[row, :, 0], [col])
            output[row, :, 1] = np.delete(self.image[row, :, 1], [col])
            output[row, :, 2] = np.delete(self.image[row, :, 2], [col])
        self.image = output
        self.image_width -= 1

    def add_seam(self, seam):
        temp_img = np.zeros((self.image_height, self.image_width+1, 3))
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

    def update_seams(self, remaining_seams, current_seam):
        output = []
        for seam in remaining_seams:
            seam[seam >= current_seam] += 2
            output.append(seam)
        return output