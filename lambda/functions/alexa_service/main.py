"""
Main AWS lambda function, based off of the Python Alexa template
provided by Amazon.
"""

from __future__ import print_function

import boto3

# I don't know of a better way to keep this in sync with
# alexa_meta/custom_slot.txt besides just checking. So uh,
# check pls.
CUSTOM_SLOT_WORDS = [
    'clean',
    'dirty',
    'washed',
    'unwashed',
    'being cleaned',
]

dynamo = boto3.resource('dynamodb')
table = dynamo.Table('dishes_io')


def handle(event, context):
    """
    Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """
    print("event.session.application.applicationId=" +
          event['session']['application']['applicationId'])


    # Uncomment this if statement and populate with your skill's application ID to
    # prevent someone else from configuring a skill that sends requests to this
    # function.
    # if (event['session']['application']['applicationId'] !=
    #         "amzn1.echo-sdk-ams.app.[unique-value-here]"):
    #     raise ValueError("Invalid Application ID")

    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])


def on_session_started(session_started_request, session):
    """
    Called when the session starts.
    """

    print("on_session_started requestId=" + session_started_request['requestId']
          + ", sessionId=" + session['sessionId'])


def on_launch(launch_request, session):
    """
    Called when the user launches the skill without specifying what they
    want to do.
    """

    print("on_launch requestId=" + launch_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    return help_response()

def on_intent(intent_request, session):
    """
    Called when the user specifies an intent for this skill
    """

    print("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'])

    intent = intent_request['intent']
    user = session['user']['userId']
    intent_name = intent_request['intent']['name']

    # This is basically like the "router" for the various intents
    # that we've built out.
    if intent_name == "GetDishStatus":
        return get_dish_status(intent, user)
    elif intent_name == "SetDishStatus":
        return set_dish_status(intent, user)
    elif intent_name == "AMAZON.HelpIntent":
        return help_response()
    else:
        raise ValueError("Invalid intent: {}".format(intent_name))


def on_session_ended(session_ended_request, session):
    """
    Called when the user ends the session.
    Is not called when the skill returns should_end_session=true
    """
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])

# --------------- Functions that control the skill's behavior ------------------

def get_dish_status(request, user):
    """
    Query the user in DynamoDB table, and check if the dishes are clean.
    """
    print(request)
    print(user)

    db_response = table.get_item(
        Key={"user": user}
    )
    try:
        status = db_response['Item']['status']
    except KeyError:
        return build_response(
            {},
            build_speechlet_response(
                "My memory is fuzzy, are your dishes clean or dirty?"
            )
        )

    return build_response(
        {},
        build_speechlet_response(
            "The dishes are {}".format(status)
        )
    )

def set_dish_status(request, user):
    """
    Set the status of the dishes for the user.
    """
    print(request)
    print(user)

    try:
        status = request['slots']['status']['value']
    except KeyError:
        return help_response()

    if status not in CUSTOM_SLOT_WORDS:
        return build_response(
            {},
            build_speechlet_response(
                "Sorry, I don't understand {}. Try saying clean or dirty.".format(status)
            )
        )

    dish_status = {
        "user": user,
        "status": status,
    }
    table.put_item(Item=dish_status)
    return build_response(
        {},
        build_speechlet_response(
            "Ok, the dishes are {}.".format(status)
        )
    )


def help_response():
    """
    Builds speech output that returns the directions for using the app.
    """
    return build_response(
        {},
        build_speechlet_response(
            ("Ask about the dishes! For example: Alexa, ask the dishwasher if it's clean. "
             "Alexa, tell the dishwasher that it's dirty. "
             "Alexa ask the dishwasher the status of the dishes.")
        )
    )

# --------------- Helpers that build all of the responses ----------------------

def build_speechlet_response(output, card_title=None, card_content=None, reprompt='',
                             should_end_session=True):
    """
    Contructs ``response`` dictionary with the proper struture to allow
    Alexa to talk to the user. Optionally takes ``card_title`` and
    ``card_content`` to build out a response viewable in the Alexa iOS
    or Android app.
    """
    response = {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt
            }
        },
        'shouldEndSession': should_end_session
    }

    if card_title and card_content:
        response['card'] = {
            'type': 'Simple',
            'title': card_title,
            'content': card_content
        }

    return response

def build_response(session_attributes, speechlet_response):
    """
    Inserts ``speechlet_response`` dictionarty into full Alexa Skills
    kit JSON response.

    TODO: maybe conflate with ``build_speechlet_response()``?
    """
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }
