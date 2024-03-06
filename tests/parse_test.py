import pytest
from celery_workers.src.api.parse import read_pdf

def test_read_pdf():
    result = read_pdf('../tests/test.pdf')
    print(result)
    assert ['Software Requirements for 5SENG001W 1 Software development For the tutorial exercises, you will need to implement various algorithms. We will usually provide a skeleton which provides things like a main function or ﬁle I/O. The exercises can be completed using either Java or C++. For this you will need a suitable development environment, which could be • An IDE such as Netbeans or Visual Studio • A regular text editor plus compiler suite (e.g. JDK or gcc) The computers in the labs will have Netbeans and Visual Studio installed; if you want to move projects between them and your own computer, using the same environment is going to be helpful. Both are available for free: • Netbeans downloads • Visual Studio downloads (I recommend sticking with the 2019 version for now) For the coursework, you will only be expected to submit a short report and some source code (.java ﬁles or .cpp and .h ﬁles, respectively), so your choice of environment should make no diﬀerence. 2 Other software In order to write your coursework report, some tool that lets you create pdf documents (like MS word or LaTeX) will be needed. You will also need to be able to draw some simple diagrams (graphs or trees). I recommend using the diagrams.net app (previously known as draw.io). 1 '] == result


