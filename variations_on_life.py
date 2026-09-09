
# Here you can define your original update function
# that controls whether each cell is set to be alive
# or dead! Make sure it has two inputs and returns
# a value for all possible inputs!










# Here you can paste in any other groups functions if you want!











if __name__ == '__main__':
    # Here I am including some testing for all the possible cases. Note that I do
    # not know what you will name your function, so you'll have to search and replace
    # the placeholder function names below. If all of the below print 0 or 1, then
    # you know your function works for all possible inputs!

    # Initially off, with all number of neighbors
    print(your_func(0, 0))
    print(your_func(0, 1))
    print(your_func(0, 2))
    print(your_func(0, 3))
    print(your_func(0, 4))
    print(your_func(0, 5))
    print(your_func(0, 6))
    print(your_func(0, 7))
    print(your_func(0, 8))

    # Initially on, with all number of neighbors
    print(your_func(1, 0))
    print(your_func(1, 1))
    print(your_func(1, 2))
    print(your_func(1, 3))
    print(your_func(1, 4))
    print(your_func(1, 5))
    print(your_func(1, 6))
    print(your_func(1, 7))
    print(your_func(1, 8))
