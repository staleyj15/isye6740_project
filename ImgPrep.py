from PIL import Image
from skimage import color, filters, feature
import numpy as np
import math
import matplotlib.pyplot as plt
import os
import re


def file_names(directory):

    """
    store all file names in list for processing
    """

    paths = os.listdir(directory)
    return [
        directory + "/" + file for file in paths if re.search(".jpg", file) is not None
    ]


def read_img(img_paths, indx):

    """
    read in image and store as array
    """
    
    pattern1 = re.compile('_Set' + str(indx) + '_')
    pattern2 = re.compile('_Set' + str(indx) + '\.')
    for path in img_paths:
        if pattern1.search(path) is not None:
            img = Image.open(path)
            img_array = np.array(img)
            img.close()
            return img_array
        elif pattern2.search(path) is not None:
            img = Image.open(path)
            img_array = np.array(img)
            img.close()
            return img_array

def reshape_array(arr, starting_dim):

    """
    flatten array to (shape # of pixels, 3)
    """
    if starting_dim == 3:
        return np.reshape(arr, (arr.shape[0] * arr.shape[1], arr.shape[2]), order="C")
    else:
        return np.reshape(arr, (1, arr.shape[0] * arr.shape[1]), order = "C")


def split_img(arr, nrow, ncol):

    """
    split image into nrow by ncol smaller images
    """

    def find_splits(shape, num):
        split = shape // num
        return [split * i for i in range(1, num)]

    def equal_pixels(list_arr, ax):
        extra = list_arr[-1].shape[ax] - list_arr[0].shape[ax] + 1
        rem_indx = [list_arr[-1].shape[ax] - n for n in reversed(range(1, extra))]
        replace = np.delete(list_arr[-1], rem_indx, axis=ax)
        list_arr.pop(-1)
        return list_arr + [replace]

    pieces = []
    rows = equal_pixels(np.split(arr, find_splits(arr.shape[0], nrow)), 0)

    for row in rows:
        cols = equal_pixels(np.split(row, find_splits(row.shape[1], ncol), axis=1), 1)
        pieces += cols

    return pieces


def remove_background(arr):
    
    """
    remove background from image
    """
    
    img = color.rgb2gray(arr)
    sobel = filters.sobel(img)
    blurred = filters.gaussian(sobel, sigma=12)

    bgremoved = arr.copy()
    for i in range(bgremoved.shape[0]):
        for j in range(bgremoved.shape[1]):
            if blurred[i,j] <= 0.016:
                bgremoved[i,j] = [0, 0, 0]
                
    return bgremoved


def fix_edges(arr, indx, shape, replace_indx = 28):
    
    '''
    remove leftover scanner background from edges of picture
    '''
    
    px0, px1, px2 = shape
    if indx % 20 <=3:
        arr[:replace_indx] = np.zeros((replace_indx, px1, px2), dtype = int)
    elif indx % 4 == 3:
        arr[:,-replace_indx:] = np.zeros((px0, replace_indx, px2), dtype = int)
    return arr


def glcmm(arr):
    
    """
    create gray level co-occurence matrix for image with background removed and calculate texture features
    """
    coeffs = np.array([0.2125, 0.7154, 0.0721])
    angs = [0, np.pi/8, np.pi/4, (3*np.pi)/8]
    
    img = np.round_(arr @ coeffs).astype(int)
    P = feature.greycomatrix(img, [1], angs, levels=256, symmetric=True)
    P2 = np.empty([P.shape[0]-1,P.shape[1]-1,P.shape[2],P.shape[3]], dtype = int)
    for i in range(P.shape[2]):
        for j in range(P.shape[3]):
            P2[:,:,i,j] = P[1:,1:,i,j]
    
    features = np.array([])
    features = np.append(features, feature.greycoprops(P2, 'contrast').flatten())
    features = np.append(features, feature.greycoprops(P2, 'dissimilarity').flatten())
    features = np.append(features, feature.greycoprops(P2, 'homogeneity').flatten())
    features = np.append(features, feature.greycoprops(P2, 'ASM').flatten())
    features = np.append(features, feature.greycoprops(P2, 'energy').flatten())
    features = np.append(features, feature.greycoprops(P2, 'correlation').flatten())
    features = np.nan_to_num(features)
    
    return features


def flatten_arrays(arr_list):
    
    px0, px1, px2 = arr_list.shape
    centers_flattened = np.zeros((px0, px1 * px2))
    
    for i in range(px0):
        centers_flattened[i,:] = reshape_array(arr_list[i,:,:], starting_dim = 2)
    
    return centers_flattened
    