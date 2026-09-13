import pyjson5

class MyQueue:
    def __init__(self):
        pass

    @property
    def data(self):
        with open('queue.jsonc', 'r') as f:
            return pyjson5.load(f)

    @property
    def queue(self):
        return self.data.get('queue', [])

    @property
    def processing(self):
        return self.data.get('processing', [])
        
    @processing.setter
    def processing(self, value):
        self.data['processing'] = value

    def consume(self):
        if self.queue:
            item = self.queue.pop(0)
            self.data['processing'].append(item)
            return 
        else:
            return None


if __name__ == "__main__":
    myqueue = MyQueue()
    obj = myqueue.consume()
    print(obj)
