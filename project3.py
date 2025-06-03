import os

# Select the diresctory whose contant you want to list
diresctory_path = '/'

# Use the od module to list the diresctory contant
contants = os.listdir(diresctory_path)

# print the contants of the diresctory
print (contants)
