from src.manager import Manager

def tester():
    URL = "https://download.samplelib.com/mp4/sample-15s.mp4"

    manager = Manager(URL)

    manager.start_download()

tester()