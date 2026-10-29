import io
import numpy as np
from PIL import Image
from backend.privacy import Detector, Finding


def test_public_name_policy_does_not_exempt_known_private_values(monkeypatch):
    detector=Detector()
    monkeypatch.setattr(detector,'detect',lambda *args,**kwargs:[Finding('PERSON',0,12,'presidio','test')])
    assert detector.sanitize('Ada Lovelace',public_context=True)[0]=='Ada Lovelace'
    assert 'Ada Lovelace' not in detector.sanitize('Ada Lovelace',known=['Ada Lovelace'],public_context=True)[0]
    assert 'Ada Lovelace' not in detector.sanitize('Ada Lovelace')[0]


def test_public_policy_still_masks_strong_identifiers():
    detector=Detector()
    text='Contact person@example.test and use ABCDE1234F or 4111 1111 1111 1111'
    safe,_=detector.sanitize(text,public_context=True)
    assert 'person@example.test' not in safe
    assert 'ABCDE1234F' not in safe
    assert '4111 1111 1111 1111' not in safe


def test_public_faces_allowed_only_inside_selected_public_region():
    detector=Detector()
    class Face:
        def setInputSize(self,size):pass
        def detect(self,image):return None,np.array([[10,10,20,20],[70,70,20,20]])
    detector.face=Face()
    image=Image.new('RGB',(100,100),'white');data=io.BytesIO();image.save(data,format='PNG')
    assert len(detector.visual_boxes(data.getvalue()))==2
    boxes=detector.visual_boxes(data.getvalue(),public_regions=[{'x':0,'y':0,'width':50,'height':50}])
    assert len(boxes)==1 and boxes[0]['x']==70
