# coding=utf-8
# Copyright 2018-2022 EVA
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
from pathlib import Path
from test.markers import windows_skip_marker

from mock import MagicMock, patch

from eva.readers.opencv_reader import OpenCVReader
from eva.utils.generic_utils import (
    generate_file_path,
    is_gpu_available,
    load_udf_class_from_file,
    str_to_class,
    validate_kwargs,
)


class ModulePathTest(unittest.TestCase):
    def test_helper_validates_kwargs(self):
        with self.assertRaises(TypeError):
            validate_kwargs({"a": 1, "b": 2}, ["a"], "Invalid keyword argument:")

    def test_should_return_correct_class_for_string(self):
        vl = str_to_class("eva.readers.opencv_reader.OpenCVReader")
        self.assertEqual(vl, OpenCVReader)

    def test_should_return_correct_class_for_path(self):
        vl = load_udf_class_from_file("eva/readers/opencv_reader.py", "OpenCVReader")
        # Can't check that v1 = OpenCVReader because the above function returns opencv_reader.OpenCVReader instead of eva.readers.opencv_reader.OpenCVReader
        # So we check the qualname instead, qualname is the path to the class including the module name
        # Ref: https://peps.python.org/pep-3155/#rationale
        assert vl.__qualname__ == OpenCVReader.__qualname__

    def test_should_return_correct_class_for_path_without_classname(self):
        vl = load_udf_class_from_file("eva/readers/opencv_reader.py")
        assert vl.__qualname__ == OpenCVReader.__qualname__

    def test_should_raise_on_missing_file(self):
        with self.assertRaises(RuntimeError):
            load_udf_class_from_file("eva/readers/opencv_reader_abdfdsfds.py")

    def test_should_raise_if_class_does_not_exists(self):
        with self.assertRaises(RuntimeError):
            # eva/utils/s3_utils.py has no class in it
            # if this test fails due to change in s3_utils.py, change the file to something else
            load_udf_class_from_file("eva/utils/s3_utils.py")

    def test_should_raise_if_multiple_classes_exist_and_no_class_mentioned(self):
        with self.assertRaises(RuntimeError):
            # eva/utils/generic_utils.py has multiple classes in it
            # if this test fails due to change in generic_utils.py, change the file to something else
            load_udf_class_from_file("eva/utils/generic_utils.py")

    def test_should_use_torch_to_check_if_gpu_is_available(self):
        # Emulate a missing import
        # Ref: https://stackoverflow.com/a/2481588
        try:
            import builtins
        except ImportError:
            import __builtin__ as builtins
        realimport = builtins.__import__

        def missing_import(name, globals, locals, fromlist, level):
            if name == "torch":
                raise ImportError
            return realimport(name, globals, locals, fromlist, level)

        builtins.__import__ = missing_import
        self.assertFalse(is_gpu_available())

        # Switch back to builtin import
        builtins.__import__ = realimport
        is_gpu_available()

    @windows_skip_marker
    @patch("eva.utils.generic_utils.ConfigurationManager")
    def test_should_return_a_random_full_path(self, mock_conf):
        mock_conf_inst = MagicMock()
        mock_conf.return_value = mock_conf_inst
        mock_conf_inst.get_value.return_value = "eva_datasets"
        expected = Path("eva_datasets").resolve()
        actual = generate_file_path("test")
        self.assertTrue(actual.is_absolute())
        # Root directory must be the same, filename is random
        self.assertTrue(expected.match(str(actual.parent)))

        mock_conf_inst.get_value.return_value = None
        self.assertRaises(KeyError, generate_file_path)
