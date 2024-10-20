#===- MLInference.py - ACPO Python ML Inference    ----------------------===//
#
# Part of the LLVM Project, under the Apache License v2.0 with LLVM Exceptions.
# See https://llvm.org/LICENSE.txt for license information.
# SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
#
# Copyright (C) 2021-2023. Huawei Technologies Co., Ltd. All rights reserved.
#
#===----------------------------------------------------------------------===//
from abc import ABC, abstractmethod
from sklearn.feature_selection import *
import numpy as np
import os
import re
import torch
# import tensorflow as tf
from ACPOmodel.src.models import NetFC




# Control ACPO log messages
#   0 = all messages are printed to stdout (defualt)
#   1 = all mesages are disabled
if os.environ.get('ACPO_LOG_LVL') is None:
  os.environ['ACPO_LOG_LVL'] = '0'

def ACPO_LOG(msg):
  """
  All print statment should be wrapped by ACPO_LOG()
    """
  if os.environ.get("ACPO_LOG_LVL") == '0':
    print(msg)
  else:
    pass


# Force to use CPU only
#os.environ['CUDA_VISIBLE_DEVICES'] = '-1'

# Set the memory growth of GPU
# gpus = tf.config.list_physical_devices('GPU')
# if gpus:
#   # Restrict TensorFlow to only allocate 1GB of memory on the first GPU
#   try:
#     tf.config.set_logical_device_configuration(
#         gpus[0], [tf.config.LogicalDeviceConfiguration(memory_limit=1000)])
#     logical_gpus = tf.config.list_logical_devices('GPU')
#     ACPO_LOG(len(gpus), "Physical GPUs,", len(logical_gpus), "Logical GPUs")
#   except RuntimeError as e:
#     # Virtual devices must be set before GPUs have been initialized
#     ACPO_LOG(e)

# Control the TensorFlow junk warnings
#   0 = all messages are logged (default behavior)
#   1 = INFO messages are not printed
#   2 = INFO and WARNING messages are not printed
#   3 = INFO, WARNING, and ERROR messages are not printed
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

field_name_set = {
    "modelname", "features", "outputs", "signature", "modeldirectory",
    "outputkey", "modelinference"
}

def get_torch_model(model_dir):
  pass





def get_imported_and_infer(model_dir, signature):
  """
  Return the imported model and infer function using the
  given model_dir and signature
  """
  model_path = os.path.join(os.path.dirname(__file__), model_dir) + "modelfi.pth"

  print(model_path)
  # imported = tf.saved_model.load(model_path)
  imported = NetFC()
  state_dict = torch.load("/Users/lvyinrun/workspace/openEuler/ACPO_zm/ACPOmodel/src/log/inline_modelV0.0/modelfi.pth", weights_only=False)
  imported.load_state_dict(state_dict)
  # imported = torch.load(model_path)
  print(imported)
  return imported
  # infer = imported.signatures[signature]
  # print(infer)
  # return (imported, infer)


def get_field_name(line):
  return line.split('=')[0].strip()


def get_field_value(line):
  return line.split('=')[1].strip()


def get_model_name(model_spec_file):
  model_spec_file_path = os.path.join(os.path.dirname(__file__),
                                      model_spec_file)
  f = open(model_spec_file_path, "r")
  line = ""
  while (True):
    line = f.readline()
    if (line.strip() != ""):
      break
  model_name = get_field_value(line)
  return model_name


def load_model(model_spec_file):
  """
  Load a model with information specified in model_spec_file,
  and return the information back to the interface so that
  it can be stored in the internal dictionary
  """
  model_spec_file_path = os.path.join(os.path.dirname(__file__),
                                      model_spec_file)
  f = open(model_spec_file_path, "r")
  lines = f.readlines()
  model_info_dict = {}
  for line in lines:
    if (line.strip() == "" or line.startswith('#')):
      continue
    field_name = get_field_name(line).lower()
    field_value = get_field_value(line)
    print(field_name, field_value)
    if (field_name not in field_name_set or field_value == ""
        or model_info_dict.get(field_name) is not None):
      print("shit")
      return ()
    else:
      model_info_dict[field_name] = field_value
  if (set(model_info_dict.keys()) != field_name_set):
    return ()
  feature_pair = re.findall('\{[^\}]*\}', model_info_dict.get('features'))
  feature_pair = list(
      map(lambda s: tuple(re.findall('[\-A-Za-z\_0-9]+[^,|^\{|^\}]', s)),
          feature_pair))
  feature_list = list(map(lambda l: l[0], feature_pair))
  output_pair = re.findall('\{[^\}]*\}', model_info_dict.get('outputs'))
  output_list = list(
      map(lambda s: tuple(re.findall('[\-A-Za-z\_0-9]+[^,|^\{|^\}]', s)),
          output_pair))
  output_str_list = list(map(lambda s: s[0] + ' ' + s[1], output_list))

  model_info_dict['featurepair'] = feature_pair
  model_info_dict['outputlist'] = output_list
  model_dir = model_info_dict.get('modeldirectory')
  signature = model_info_dict.get('signature')

  imported = get_imported_and_infer(model_dir, signature)

  # imported_and_infer = get_imported_and_infer(model_dir, signature)
  # imported = imported_and_infer[0]
  # infer = imported_and_infer[1]
  infer = "unknown"
  model_info_dict['imported'] = imported
  model_info_dict['infer'] = infer
  # TODO: use a pickle object to load into the classes_dict automatically (later)
  # v4.6 classes (7 UP.Counts only, no more UP.Type prediction)
  if "lu" in model_spec_file:
    model_info_dict['classesdict'] = {
        0: (0, 3),
        1: (2, 3),
        2: (4, 3),
        3: (8, 3),
        4: (16, 3),
        5: (32, 3),
        6: (64, 3)
    }
  model_info_str = model_info_dict.get('modelname') + "," +\
    str(len(feature_list)) + "," + ",".join(feature_list) + "," +\
    str(len(output_list)) + "," + ",".join(output_str_list) + "," +\
    model_info_dict.get('signature')
  return (model_info_dict, model_info_str)


def create_MLInference(model_inference, model_dir, infer, output_key, classes_dict,
                       output_name):

  if "FIInference" in model_inference:
    from FIInference import FIInference
    return FIInference(model_dir, infer, output_key, classes_dict, output_name)
  elif "LUInference" in model_inference:
    from LUInference import LUInference
    return LUInference(model_dir, infer, output_key, classes_dict, output_name)
  else:
    ACPO_LOG("No model type of: " + model_inference)
    exit(1)


class MLInference(ABC):

  def __init__(self, model_dir, infer, output_key, classes_dict, output_names):
    self.model_dir = model_dir
    self.infer = infer
    self.output_key = output_key
    self.classes_dict = classes_dict
    self.output_names = output_names
    self.features = []

  def runInfer(self):
    return self.inference()

  # Each model could have different ways to prepare their features and the
  # infer() function could take different parameters.
  @abstractmethod
  def inference(self):
    pass

  @abstractmethod
  def prepare_features(self):
    pass

  def set_feature(self, index, value):
    """
      Set the feature at the specified index with a new value.
      """
    self.features[index] = value

  def set_features(self, sent_features):
    """
      Set the features at the specified indices with new values.
      sent_features is a list of (index, value) tuples.
      """
    for pair in sent_features:
      self.set_feature(pair[0], pair[1])

  def initialize_features(self, sent_features):
    """
      Initialize features and activate a new model.
      The global features list will be replaced with a new list.
      sent_features is a list of (index, value) tuples.
      """
    self.features = []
    for x in range(len(sent_features)):
      self.features.append(0)
    self.set_features(sent_features)

if __name__ == "__main__":
  inference()

