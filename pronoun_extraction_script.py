# imports
import requests
import numpy as np
import cv2
NAMEAPI_KEY="c5daf3adac2a3e85791630c643d55611-user1"
url = ("http://api.nameapi.org/rest/v5.3/genderizer/persongenderizer?"
    f"apiKey={NAMEAPI_KEY}"
)

FACE_THRESHOLD_MALE=0.35
FACE_THRESHOLD_FEMALE=0.65
from cltl_face_all.face_alignment import FaceDetection
from cltl_face_all.arcface import ArcFace
from cltl_face_all.agegender import AgeGender

ag = AgeGender(device='cpu')
af = ArcFace(device='cpu')
fd = FaceDetection(device='cpu', face_detector='blazeface')

def get_visual_gender(image_filepath):
    """
    Reads image
    Load Tae's gender-age code. https://github.com/leolani/cltl-face-all
    Extract gender
    Translate gender  to Male, Female, Unknown/Neutral (0,1,2)
    Maybe we need a function to read the image file path to the format needed for Tae's module

    NOTE: THRESHOLDS ARE ASSUMED AND UNTESTED!

    :param image_filepath: string to filepath
    :return: 0,1,2 for male, female, unknown
    """
    img_BGR = cv2.imread(image_filepath)
    img = cv2.cvtColor(img_BGR, cv2.COLOR_BGR2RGB)

    bboxes = fd.detect_faces(img[np.newaxis, ...])
    landmarks = fd.detect_landmarks(img[np.newaxis, ...], bboxes)
    faces = fd.crop_and_align(img[np.newaxis, ...], bboxes, landmarks)

    # There is only one image per batch. fd returns a list
    bbox = bboxes[0]
    landmark = landmarks[0]
    face = faces[0]
    if len(bbox) > 0:
        #print(f"number of faces in this frame: {len(bbox)}")

        # ag and af return a np.ndarray
        _, predicted_gender = ag.predict(face)
        print(predicted_gender)
        if predicted_gender < FACE_THRESHOLD_MALE:
            return 0 #for male
        elif predicted_gender > FACE_THRESHOLD_FEMALE:
            return 1 #for female
        else:
            return 2 #fer unknown



def get_name_gender(name_string):
    """
    Use (harvard) api.
    Translate result to 0,1,2 for gender coding.
    :param name_string: The name as a string
    :return: 0,1,2 for male, female, unknown
    """
    # Dict of data to be sent to the RESTapi of NameAPI.org:
    payload = {
        "context": {
            "priority": "REALTIME",
            "properties": []
        },
        "inputPerson": {
            "type": "NaturalInputPerson",
            "personName": {
                "nameFields": [
                    {
                        "string": f"{name_string}",
                        "fieldType": "GIVENNAME"
                    }]
            },
            "gender": "UNKNOWN"
        }
    }
    # Proceed, only if no error:
    try:
        # Send request to NameAPI.org by doing the following:
        # - make a POST HTTP request
        # - encode the Python payload dict to JSON
        # - pass the JSON to request body
        # - set header's 'Content-Type' to 'application/json' instead of
        #   default 'multipart/form-data'
        resp = requests.post(url, json=payload)
        resp.raise_for_status()
        # Decode JSON response into a Python dict:
        resp_dict = resp.json()
        print(resp_dict)
        name_gender = resp_dict['gender']
        if name_gender == 'MALE':
            name_gender_int = 0
        elif name_gender == 'FEMALE':
            name_gender_int = 1
        elif name_gender == 'NEUTRAL':
            name_gender_int= 2
        elif name_gender == 'UNKNOWN':
            name_gender_int = 2
        return name_gender_int
    except requests.exceptions.HTTPError as e:
        print("Bad HTTP status code:", e)
    except requests.exceptions.RequestException as e:
        print("Network error:", e)


def greeting_script():
    """
    Script where Leolani introduces herself and asks who are you

    :return: tuple(name, pronouns) or tuple(name, None)
    """
    name = None
    pronouns = None

    print("Hi! I'm Leolani, my pronouns are she/her. I love getting to know new people.")
    print("While I am learning, please fill in your name and pronouns in the following format: 'name, pro/nouns' or just 'name'")
    answer = input("Who are you? \n")

    if "," in answer:
        name, pronouns = answer.split(", ")
        print(f"Nice to meet you, {name}. Your pronouns are {pronouns}")
    else:
        name = answer
        # pronouns remain unchanged (None)
        print(f"Nice to meet you, {name}.")
        # TODO: remove later
        print("You have not specified your pronouns.")

    return name, pronouns

def suggest_pronouns_script(suggesting_pronouns):
    """
    Verifying whether suggested pronouns are okay.
    :param suggesting_pronouns: 0,1,2 relating to gender of visual input
    :return: pronouns
    """
    pronouns = None

    pronoun_ok = input(f"Would you like me to refer to you as {suggesting_pronouns}? y/n \n")

    if pronoun_ok == "y":
        pronouns = suggesting_pronouns
    else:
        print("My apologies, I am still learning about the human world.")
        pronouns = input("Which pronouns would you like me to use to refer to you? \n")

    return pronouns

def pronoun_retrieving_script(name_gender, visual_gender):
    """
    Assumes or asks for pronouns.
    This is where the scenarios go if the pronouns were not given in the introduction.
    :param name_gender: 0,1,2 relating to gender of name
    :param visual_gender: 0,1,2 relating to gender of visual input
    :return: pronouns
    """
    # Set global variable
    pronouns = None

    # If gender of name is unknown, ask for pronouns, no suggestion
    if name_gender == 2:
        # TODO remove first print statement
        print("I cannot detect gender based on your name.")

        pronouns = input("Which pronouns would you like me to use to refer to you? ")

    # If gender of name and visual match, assume pronouns
    elif name_gender == visual_gender:
        # TODO: remove print statement
        print("The gender of your name and visual match. I will assume your pronouns.")

        # TODO: check if number coding is correct
        if name_gender == 0:
            pronouns = "he/him"
        elif name_gender == 1:
            pronouns = "she/her"

    else:
        # TODO remove first print statement
        print("There is a mismatch between the gender of your name and visual.")

        print("I have been taught that there are different ways that humans like to be referred as.")
        if name_gender == 0:
            suggested_pronouns = "he/him"
            pronouns = suggest_pronouns_script(suggested_pronouns)

        elif name_gender == 1:
            suggested_pronouns = "she/her"
            pronouns = suggest_pronouns_script(suggested_pronouns)

    return pronouns



def create_triple(name_string, pronouns_string):
    """
    Create triple in Leolani brain format.
    Probably something like: LeolaniWorld:Quirine, property:has_pronouns, value:she/her.
    # How do we store the pronouns? Options: tuple of strings ("she", "her"), string "she/her", int 0, 1 or 2 (but then its a predefined finite set.

    :param name_string: String of name to store in Leolani brain (is this needed to form the triple
    :param pronouns_string: string of pronouns
    :return: triple in Leolani brain format
    """
    #Is this usefull?
    return (f'LeolaniWolrd:{name_string.lower()}', 'has_pronouns', f'pronouns:{pronouns_string.lower()}')



def store_triple(triple_object):
    """
    Store triple object in folder and file
    :param triple_object:
    :return: nothing, saved triple in correct location
    """

def main_inprogress():
    #temp_visual_gender = 1
    image_path='merel_test.jpg'

    # Set global variables
    name = None
    pronouns = None

    # Leolani introduces herself
    name, pronouns = greeting_script()
    # If pronouns are not given
    if pronouns == None:
        visual_gender = get_visual_gender(image_path)
        name_gender = get_name_gender(name)

        # Run through script to extract pronouns either by asking or assuming
        pronouns = pronoun_retrieving_script(name_gender, visual_gender)

    print(create_triple(name, pronouns))

if __name__ == "__main__":
    main_inprogress()
