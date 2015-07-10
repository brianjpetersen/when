import datetime



class MetaClass(type):
    
    def __new__(metaname, classname, baseclasses, attrs):
        return super(MetaClass, metaname).__new__(metaname, classname, baseclasses, attrs)
    
    def __call__(self, *args):
        print('in metaclass __call__', self, args)
        return super(MetaClass, self).__init__(self, *args)



class Class(datetime.datetime):
    
    def __new__(cls):
        # return nonsense to allow the following two conditions to be met:
        # 
        # 1. 
        return datetime.datetime.__new__(cls, 1111, 2, 3, 4, 5, 6, 777777)
    
    def __init__(self):
        print('in class __init__')
        self.test = 'test'
        
    @property
    def __class__(self):
        return Class
        
    @property
    def __bases__(self):
        return (datetime.datetime, )


c = Class()
print(c.__bases__, Class.__bases__)
print(c.__dict__)
print(dir(c))


print(issubclass(Class, datetime.datetime))
print(isinstance(c, datetime.datetime))

