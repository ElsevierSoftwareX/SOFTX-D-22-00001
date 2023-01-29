# Hetool
A Half-Edge Topological Object-Oriented Library for generic 2-D geometric modelling.

## Description
An object-oriented architecture of a topological data structure allowing high-level interactive two-dimensional (2-D) geometric modeling called HETOOL is introduced in this repository. The implementation is based on the well-known half-edge data structure for 2-manifold solids, which is adapted here for dealing efficiently with general 2-D models and planar subdivisions, very commons in science and engineering problems. The HETOOL was developed in Python. The developed package presents a dynamic data structure that performs the automatic tessellation of the modeled geometric elements. The library offers many features and facilities to the user, allowing the use of the package even without the user having knowledge about the topological concepts involved in the implementation of this data structure. In addition, the library offers flexibility in the configuration of new attributes, enabling the creation of these elements in a simple and fast way from a file in JSON format. This versatility in creating new attributes allows the application of this package to solve several problems present in the scientific world. This package presents methods that allow the modeling of two-dimensional solids by inserting points and segments. Patche (planar regions) are automatically generated from the closing of a segment path. The library also offers methods that deal with the creation and configuration of specific attributes that can be assigned to geometric entities.

## Requirements
To use this library it is necessary to install the following libraries:
- [ ] [Python](https://www.python.org/)
- [ ] [JSON](https://docs.python.org/3/library/json.html)

To use the examples, it is necessary to install the following libraries:
- [ ] [PyOpenGL](https://pypi.org/project/PyOpenGL/)
- [ ] [PyQt5](https://pypi.org/project/PyQt5/)
- [ ] [Matplotlib](https://matplotlib.org/)
- [ ] [NumPy](https://numpy.org/)

## Installation and How to Use
To install and use the library, just download the files and copy the hetool folder to the desired directory of use. For beginners it is highly recommended to use the package through the methods present in the hetool\include\hetool file. This file presents a documentation of the main functions present in this library. For people more familiar with the package, just create and use the HeController, HeModel and HeView classes.


## Usage
This repository presents some simple examples of using the Hetool library. These examples demonstrate all the commands needed for inserting points and segments, creating holes, and creating and setting new attributes. These examples can be found in the examples folder. For the use of these examples download the libraries indicated in the requirements.

Note: HE_curve collector example may not work properly on computers with HiDPI screen.

## Acknowledgment
This work was carried out with the support of the Coordenação de Aperfeiçoamento de Pessoal de Nível Superior - Brasil (CAPES) - Financing Code 001.

## License
GNU LGPLv3

## Authors
Main developer:

- Danilo Silva Bomfim - dsbomfim2@hotmail.com

Contributors:

- André M. B. Pereira
- Luiz F. Bez
- Luiz F. Martha
- Pedro C. F. Lopes
- Rodrigo L. Soares

