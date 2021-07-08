import logging

def setup_logger(name, log_file, level=logging.INFO):
  """To setup as many loggers as you want"""

  handler = logging.FileHandler(log_file)
  formatter = logging.Formatter('%(levelname)s %(asctime)s %(funcName)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
  handler.setFormatter(formatter)

  logger = logging.getLogger(name)
  logger.setLevel(level)
  logger.addHandler(handler)

  return logger