from seamCarver import SeamCarver
import cv2
import time
import argparse
import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument('--image_path', type=str)
parser.add_argument('--new_width', type=int)
parser.add_argument('--new_height', type=int)
parser.add_argument('--action', type=int)
parser.add_argument('--object', type=str, default=None)
parser.add_argument('--is_show', type=bool, default=False)


def resize(output_size, carver, is_show):
    return carver.resize(output_size, is_show)

def removal(object, carver):
    return carver.removal(object)

def main():
    args = parser.parse_args()
    filename = args.image_path
    output_width = args.new_width
    output_height = args.new_height
    option = args.action
    object = args.object
    is_show = args.is_show
    output_size = (output_height, output_width)

    start_time = time.time()
    carver = SeamCarver(cv2.imread(filename))
    if option == 0:
        output_image = resize(output_size, carver, is_show)
    else:
        object = cv2.imread(object).astype(np.float64)
        output_image = removal(object, carver)
    cv2.imwrite('result.jpg', output_image)
    print(time.time() - start_time)

if __name__ == '__main__':
    main()