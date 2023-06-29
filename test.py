import requests
from pprint import pprint
import numpy as np

a = [[1,2], [2,3], [3,4,5]]
b = [x for y in a for x in y]


print(b)
