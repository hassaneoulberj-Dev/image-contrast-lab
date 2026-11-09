import io
import unittest
import zipfile
import cv2
import numpy as np
from src.processing import metrics, process, decode, demo_image, export


class ProcessingTests(unittest.TestCase):
    def test_large_pixel_difference(self):
        result = metrics(np.zeros((8, 8), np.uint8), np.full((8, 8), 255, np.uint8))
        self.assertEqual(result['MSE'], 65025)
        self.assertEqual(result['PSNR_dB'], 0)

    def test_identity_and_small_image(self):
        image = np.arange(9, dtype=np.uint8).reshape(3, 3)
        result = metrics(image, image)
        self.assertEqual(result['SSIM'], 1)
        self.assertTrue(np.isinf(result['PSNR_dB']))

    def test_constant_image(self):
        image = np.full((8, 8), 100, np.uint8)
        result = process(image)
        np.testing.assert_array_equal(result['Etirement'], image)
        np.testing.assert_array_equal(result['Gamma'], image)

    def test_invalid_file_and_16bit(self):
        with self.assertRaises(ValueError):
            decode(b'not an image')
        _, data = cv2.imencode('.png', np.zeros((8, 8), np.uint16))
        with self.assertRaises(ValueError):
            decode(data.tobytes())

    def test_export_roundtrip(self):
        images = process(demo_image())
        with zipfile.ZipFile(io.BytesIO(export(images, {'gamma': 1}))) as archive:
            self.assertEqual(len(archive.namelist()), 9)
            np.testing.assert_array_equal(decode(archive.read('CLAHE.png')), images['CLAHE'])
            self.assertIn('SSIM', archive.read('metriques.csv').decode('utf-8-sig'))


if __name__ == '__main__':
    unittest.main()
