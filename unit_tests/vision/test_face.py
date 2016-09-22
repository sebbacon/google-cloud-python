# Copyright 2016 Google Inc. All rights reserved.
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

import unittest


class TestFace(unittest.TestCase):
    def _getTargetClass(self):
        from google.cloud.vision.face import Face
        return Face

    def setUp(self):
        from unit_tests.vision._fixtures import FACE_DETECTION_RESPONSE
        self.FACE_ANNOTATIONS = FACE_DETECTION_RESPONSE['responses'][0]
        self.face_class = self._getTargetClass()
        self.face = self.face_class.from_api_repr(
            self.FACE_ANNOTATIONS['faceAnnotations'][0])

    def test_face_landmarks(self):
        self.assertEqual(0.54453093, self.face.landmarking_confidence)
        self.assertEqual(0.9863683, self.face.detection_confidence)
        self.assertTrue(hasattr(self.face.landmarks, 'left_eye'))
        self.assertEqual(1004.8003,
                         self.face.landmarks.left_eye.position.x_coordinate)
        self.assertEqual(482.69385,
                         self.face.landmarks.left_eye.position.y_coordinate)
        self.assertEqual(0.0016593217,
                         self.face.landmarks.left_eye.position.z_coordinate)
        self.assertEqual('LEFT_EYE',
                         self.face.landmarks.left_eye.landmark_type)

    def test_facial_emotions(self):
        from google.cloud.vision.face import Likelihood
        self.assertEqual(Likelihood.VERY_LIKELY,
                         self.face.emotions.joy_likelihood)
        self.assertEqual(Likelihood.VERY_UNLIKELY,
                         self.face.emotions.sorrow_likelihood)
        self.assertEqual(Likelihood.VERY_UNLIKELY,
                         self.face.emotions.surprise_likelihood)
        self.assertEqual(Likelihood.VERY_UNLIKELY,
                         self.face.emotions.anger_likelihood)

    def test_faciale_angles(self):
        self.assertEqual(-0.43419784, self.face.angles.roll)
        self.assertEqual(6.027647, self.face.angles.pan)
        self.assertEqual(-18.412321, self.face.angles.tilt)

    def test_face_headware_and_blur_and_underexposed(self):
        from google.cloud.vision.face import Likelihood
        self.assertEqual(Likelihood.VERY_UNLIKELY,
                         self.face.image_properties.blurred_likelihood)
        self.assertEqual(Likelihood.VERY_UNLIKELY,
                         self.face.headwear_likelihood)
        self.assertEqual(Likelihood.VERY_UNLIKELY,
                         self.face.image_properties.underexposed_likelihood)

    def test_face_bounds(self):
        self.assertEqual(4, len(self.face.bounds.vertices))
        self.assertEqual(748, self.face.bounds.vertices[0].x_coordinate)
        self.assertEqual(58, self.face.bounds.vertices[0].y_coordinate)

    def test_facial_skin_bounds(self):
        self.assertEqual(4, len(self.face.fd_bounds.vertices))
        self.assertEqual(845, self.face.fd_bounds.vertices[0].x_coordinate)
        self.assertEqual(310, self.face.fd_bounds.vertices[0].y_coordinate)
