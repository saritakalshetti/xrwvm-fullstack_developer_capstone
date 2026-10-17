from django.http import JsonResponse
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
import json

from .populate import initiate
from .models import CarMake, CarModel
from .restapis import get_request, analyze_review_sentiments, post_review


@csrf_exempt
def login_user(request):
    data = json.loads(request.body)
    username = data['userName']
    password = data['password']
    user = authenticate(username=username, password=password)
    data = {"userName": username}
    if user is not None:
        login(request, user)
        data = {"userName": username, "status": "Authenticated"}
    return JsonResponse(data)


def logout_request(request):
    logout(request)
    return JsonResponse({"userName": ""})


@csrf_exempt
def registration(request):
    data = json.loads(request.body)
    username = data['userName']
    try:
        User.objects.get(username=username)
        return JsonResponse({"userName": username,
                             "error": "Already Registered"})
    except User.DoesNotExist:
        user = User.objects.create_user(username=username,
                                        first_name=data['firstName'],
                                        last_name=data['lastName'],
                                        password=data['password'],
                                        email=data['email'])
        login(request, user)
        return JsonResponse({"userName": username, "status": "Authenticated"})


def get_cars(request):
    if CarMake.objects.filter().count() == 0:
        initiate()
    car_models = CarModel.objects.select_related('car_make')
    cars = [{"CarModel": c.name, "CarMake": c.car_make.name}
            for c in car_models]
    return JsonResponse({"CarModels": cars})


def get_dealerships(request, state="All"):
    if state == "All":
        endpoint = "/fetchDealers"
    else:
        endpoint = "/fetchDealers/" + state
    return JsonResponse({"status": 200, "dealers": get_request(endpoint)})


def get_dealer_details(request, dealer_id):
    endpoint = "/fetchDealer/" + str(dealer_id)
    return JsonResponse({"status": 200, "dealer": get_request(endpoint)})


def get_dealer_reviews(request, dealer_id):
    endpoint = "/fetchReviews/dealer/" + str(dealer_id)
    reviews = get_request(endpoint)
    for review_detail in reviews:
        response = analyze_review_sentiments(review_detail['review'])
        review_detail['sentiment'] = response['sentiment']
    return JsonResponse({"status": 200, "reviews": reviews})


@csrf_exempt
def add_review(request):
    if request.user.is_anonymous is False:
        data = json.loads(request.body)
        try:
            post_review(data)
            return JsonResponse({"status": 200})
        except Exception:
            return JsonResponse({"status": 401,
                                 "message": "Error in posting review"})
    return JsonResponse({"status": 403, "message": "Unauthorized"})