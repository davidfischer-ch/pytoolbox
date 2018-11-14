# -*- encoding: utf-8 -*-

# Copyright 2015-2016 Carnegie Mellon University
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Original: https://github.com/krasserm/face-recognition/blob/master/align.py

import bz2, tempfile

import cv2, dlib, numpy as np

from pytoolbox.ai.vision import utils

__all__ = ['DlibFaceDetector']

TEMPLATE = np.float32([
    (0.0792396913815, 0.339223741112), (0.0829219487236, 0.456955367943),
    (0.0967927109165, 0.575648016728), (0.122141515615, 0.691921601066),
    (0.168687863544, 0.800341263616), (0.239789390707, 0.895732504778),
    (0.325662452515, 0.977068762493), (0.422318282013, 1.04329000149),
    (0.531777802068, 1.06080371126), (0.641296298053, 1.03981924107),
    (0.738105872266, 0.972268833998), (0.824444363295, 0.889624082279),
    (0.894792677532, 0.792494155836), (0.939395486253, 0.681546643421),
    (0.96111933829, 0.562238253072), (0.970579841181, 0.441758925744),
    (0.971193274221, 0.322118743967), (0.163846223133, 0.249151738053),
    (0.21780354657, 0.204255863861), (0.291299351124, 0.192367318323),
    (0.367460241458, 0.203582210627), (0.4392945113, 0.233135599851),
    (0.586445962425, 0.228141644834), (0.660152671635, 0.195923841854),
    (0.737466449096, 0.182360984545), (0.813236546239, 0.192828009114),
    (0.8707571886, 0.235293377042), (0.51534533827, 0.31863546193),
    (0.516221448289, 0.396200446263), (0.517118861835, 0.473797687758),
    (0.51816430343, 0.553157797772), (0.433701156035, 0.604054457668),
    (0.475501237769, 0.62076344024), (0.520712933176, 0.634268222208),
    (0.565874114041, 0.618796581487), (0.607054002672, 0.60157671656),
    (0.252418718401, 0.331052263829), (0.298663015648, 0.302646354002),
    (0.355749724218, 0.303020650651), (0.403718978315, 0.33867711083),
    (0.352507175597, 0.349987615384), (0.296791759886, 0.350478978225),
    (0.631326076346, 0.334136672344), (0.679073381078, 0.29645404267),
    (0.73597236153, 0.294721285802), (0.782865376271, 0.321305281656),
    (0.740312274764, 0.341849376713), (0.68499850091, 0.343734332172),
    (0.353167761422, 0.746189164237), (0.414587777921, 0.719053835073),
    (0.477677654595, 0.706835892494), (0.522732900812, 0.717092275768),
    (0.569832064287, 0.705414478982), (0.635195811927, 0.71565572516),
    (0.69951672331, 0.739419187253), (0.639447159575, 0.805236879972),
    (0.576410514055, 0.835436670169), (0.525398405766, 0.841706377792),
    (0.47641545769, 0.837505914975), (0.41379548902, 0.810045601727),
    (0.380084785646, 0.749979603086), (0.477955996282, 0.74513234612),
    (0.523389793327, 0.748924302636), (0.571057789237, 0.74332894691),
    (0.672409137852, 0.744177032192), (0.572539621444, 0.776609286626),
    (0.5240106503, 0.783370783245), (0.477561227414, 0.778476346951)
])

TPL_MIN, TPL_MAX = np.min(TEMPLATE, axis=0), np.max(TEMPLATE, axis=0)
MINMAX_TEMPLATE = (TEMPLATE - TPL_MIN) / (TPL_MAX - TPL_MIN)


class DlibFaceDetector(object):
    """
    Use `dlib's landmark estimation <http://blog.dlib.net/2014/08/real-time-face-pose-estimation.html>`_
    to align faces.

    The alignment pre-process faces for input into a neural network.
    Faces are resized to the same size (such as 96x96) and transformed to make landmarks (such as
    the eyes and nose) appear at the same location on every image.

    Normalized landmarks:

    .. image:: ../images/dlib-landmark-mean.png
    """

    # Downloaded from http://dlib.net/files/
    DEFAULT_PREDICTOR = (
        'https://s3-eu-west-1.amazonaws.com/pytoolbox/ai/vision/face/detect/'
        'shape_predictor_68_face_landmarks.dat.bz2')

    PREDICTORS_DOWNLOAD_DIRECTORY = tempfile.gettempdir()

    #: Landmark indices.
    INNER_EYES_AND_BOTTOM_LIP = [39, 42, 57]
    OUTER_EYES_AND_NOSE = [36, 45, 33]

    def __init__(self, predictor=None):
        """
        Instantiate a :class:`DlibFaceDetector` object.

        :param predictor: The path to dlib's landmarks file.
        :type predictor: str
        """
        if predictor is None:
            predictor = self.DEFAULT_PREDICTOR
        self.predictor = self._load_predictor(predictor)
        self.detector = dlib.get_frontal_face_detector()

    def align(self, image, box, dimension=96, landmark_indices=None, landmarks=None):
        """
        Transform and align a face in an image.

        :param image: RGB image to process. Shape: (height, width, 3)
        :type image: numpy.ndarray
        :param box: Bounding box around the face to align.
        :type box: dlib.rectangle
        :type dimension: int
        :param landmark_indices: The indices to transform to.
        :type landmark_indices: list of ints
        :param dimension: The edge length in pixels of the square the image is resized to.
        :param landmarks: Detected landmark locations. \
                          Landmarks found on `box` if not provided.
        :type landmarks: list of (x,y) tuples
        :return: The aligned RGB image. Shape: (dimension, dimension, 3)
        :rtype: numpy.ndarray
        """
        if landmark_indices is None:
            landmark_indices = self.OUTER_EYES_AND_NOSE
        if landmarks is None:
            landmarks = self.find_landmarks(image, box)

        landmarks = np.float32(landmarks)
        landmark_indices = np.array(landmark_indices)

        H = cv2.getAffineTransform(
            landmarks[landmark_indices],
            dimension * MINMAX_TEMPLATE[landmark_indices])

        return cv2.warpAffine(image, H, (dimension, dimension))

    def extract_all_faces(self, image, dimension=96, landmark_indices=None):
        for box in self.get_all_faces_bounding_boxes(image):
            yield box, self.align(image, box, dimension, landmark_indices)

    def extract_largest_face(self, image, dimension=96, landmark_indices=None, skip_multi=False):
        box = self.get_largest_face_bounding_box(image, skip_multi=skip_multi)
        return box, (self.align(image, box, dimension, landmark_indices) if box else None)

    def get_all_faces_bounding_boxes(self, image):
        """
        Find all face bounding boxes in an image.

        :param image: RGB image to process. Shape: (height, width, 3)
        :type image: numpy.ndarray
        :return: All face bounding boxes in an image.
        :rtype: dlib.rectangles
        """
        try:
            return self.detector(image, 1)
        except Exception as e:
            print("Warning: {0}".format(e))
            # In rare cases, exceptions are thrown.
            return []

    def get_largest_face_bounding_box(self, image, skip_multi=False):
        """
        Find the largest face bounding box in an image.

        :param image: RGB image to process. Shape: (height, width, 3)
        :type image: numpy.ndarray
        :param skip_multi: Skip image if more than one face detected.
        :type skip_multi: bool
        :return: The largest face bounding box in an image, or None.
        :rtype: dlib.rectangle
        """
        faces = self.get_all_faces_bounding_boxes(image)
        if not skip_multi and len(faces) > 0 or len(faces) == 1:
            return max(faces, key=lambda rect: rect.width() * rect.height())

    def find_landmarks(self, image, box):
        """
        Find the landmarks of a face.

        :param image: RGB image to process. Shape: (height, width, 3)
        :type image: numpy.ndarray
        :param box: Bounding box around the face to find landmarks for.
        :type box: dlib.rectangle
        :return: Detected landmark locations.
        :rtype: list of (x,y) tuples
        """
        points = self.predictor(image, box)
        return list(map(lambda p: (p.x, p.y), points.parts()))

    def _load_predictor(self, predictor):
        predictor = utils.load_to_file(predictor)
        if predictor.endswith('.bz2'):
            decompressor = bz2.BZ2Decompressor()
            with open(predictor, 'rb') as f, tempfile.NamedTemporaryFile('wb') as g:
                g.write(decompressor.decompress(f.read()))
                return dlib.shape_predictor(g.name)
        else:
            return dlib.shape_predictor(predictor)
