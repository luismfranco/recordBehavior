from setuptools import setup, find_packages

setup(
      
      # App Info
      name = "recordBehavior",
      version = "1.0.0", 
      description = "GUI for recording behavior data in mice",
      author = "Luis M. Franco",
      author_email = "luisfran@uoregon.edu",
      license = "MIT",
      url = "https://github.com/luismfranco/recordBehavior",

      # Dependencies
      packages = find_packages(),
      python_requires = "== 3.12.7",
      install_requires = [
                          "pillow == 11.3.0",
                          "opencv-python == 4.13.0.92",
                          "pyserial == 3.5",
                          "numpy == 2.2.6",
                          "imagingcontrol4 == 1.4.0.3240",
       ],
      
      # Classifiers
      classifiers = [
                     "Development Status :: 3 - Alpha",
                     "Intended Audience :: Science/Research",
                     "Operating System :: Windows",        
                     "Programming Language :: Python :: 3.10.14",
      ],
      
)