import datetime
import uuid

from django.contrib.auth import get_user_model
from django.db.models import Avg, Count, Max, Min, Sum
from rest_framework import generics, status, permissions
from rest_framework.parsers import JSONParser
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from BookingSystem.models import Booking, Room
from BookingSystem.serializer import BookingSerializer, RoomSerializer


# viewsets
class RoomsView(ModelViewSet):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer


class BookingsView(ModelViewSet):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer


## individual views
# Room and Slot Book Views
class RoomListView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):
        res = []
        for item in Room.objects.all():
            x = {"id": item.id,
                "room_name": item.room_name,
                "school": item.school,
                "room_number": item.room_number,
                "description": item.description}
            res.append(x)
        return Response(res)

    def post(self, request):
        try:
            res, data = [], request.data
            date, start, end = data["date"], data["start"], data["end"]
            q = Booking.objects.filter(booking_date__exact=date, start_timing=start, end_timing=end).order_by('-admin_did_accept','-is_pending')
            for item in q:
                x = {"id": item.Room.id,
                     "room_name": item.Room.room_name,
                     "school": item.Room.school,
                     "room_number": item.Room.room_number,
                     "description": item.Room.description,
                     "booking_date": item.booking_date,
                     "start_timing": item.start_timing,
                     "end_timing": item.end_timing,
                     "admin_did_accept": item.admin_did_accept,
                     "is_pending": item.is_pending}
                res.append(x)
            return Response(res)

        except:
                return Response({"message": "Invalid/Bad request"}, status=status.HTTP_400_BAD_REQUEST)


class RoomDetailView(APIView):

    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            res, date, roomID = [], request.data["date"], request.data["id"]
            for item in Booking.objects.filter(booking_date__exact=date, Room__exact=roomID).order_by('start_timing', '-admin_did_accept', '-is_pending').distinct('start_timing'):
                x = {"start_timing": item.start_timing,
                     "end_timing": item.end_timing,
                     "admin_did_accept": item.admin_did_accept,
                     "is_pending": item.is_pending}
                res.append(x)
            # Create and append empty slots
            check = list(i['start_timing'] for i in res)
            start = datetime.datetime(2000, 1, 1, 8, 0, 0)
            end = datetime.datetime(2000, 1, 1, 20, 30, 0)
            delta = datetime.timedelta(hours=1, minutes=30)
            while start <= end:
                if start.time() not in check:
                    y = {"start_timing": start.time(),
                         "end_timing": (start+delta).time(),
                         "admin_did_accept": False,
                         "is_pending": False}
                    res.append(y)
                start += delta
            return Response(sorted(res, key=lambda i: i['start_timing']))
        except:
            return Response({"message": "Invalid/Bad request"}, status=status.HTTP_400_BAD_REQUEST)


class BookRoomSlotView(APIView):
    startTimes = [datetime.time(8, 0), datetime.time(9, 30), datetime.time(11, 0), datetime.time(12, 30), datetime.time(14, 0), datetime.time(15, 30), datetime.time(17, 0), datetime.time(18, 30), datetime.time(20, 0)]
    endTimes = [datetime.time(9, 30), datetime.time(11, 0), datetime.time(12, 30), datetime.time(14, 0), datetime.time(15, 30), datetime.time(17, 0), datetime.time(18, 30), datetime.time(20, 0), datetime.time(20, 30)]

    parser_classes = [JSONParser]

    def post(self, request):
        try:
            res, data = [], request.data
            try:
                purpose = data["purpose_of_booking"]
            except:
                purpose = "Purpose not provided"
            start = datetime.datetime.strptime(data["startTime"],"%H:%M:%S").time()
            end = datetime.datetime.strptime(data["endTime"], "%H:%M:%S").time()
            roomId, date = data["roomID"], data["date"]
            if (start not in BookRoomSlotView.startTimes) or (end not in BookRoomSlotView.endTimes):
                return Response("This slot does not exist. Booking not possible")

            if Booking.objects.filter(booking_date__exact=date, start_timing=start, end_timing=end, user=request.user).exclude(admin_did_accept=False, is_pending=False).count() >= 1:
                return Response("You have already booked this timing. You cannot book 2 slots at the same time", status.HTTP_409_CONFLICT)
            
            for item in Booking.objects.filter(booking_date__exact=date, Room__exact=roomId):
                if (end <= item.start_timing or start >= item.end_timing):
                    # no clashes if the entire for loop doesn't break then the following else is executed
                    continue
                elif (item.admin_did_accept == True):
                    # Already booked
                    return Response("This slot has already been booked", status=status.HTTP_306_RESERVED)
                else:
                    # empty slot with many bookings
                    room = Room.objects.get(id__exact=roomId)
                    b = Booking.objects.create(user=request.user, Room=room, booking_date=date, start_timing=start, end_timing=end, purpose_of_booking=purpose, is_pending=True)
                    return Response("Booking has been added to the already existing queue", status=status.HTTP_202_ACCEPTED)
            else:
                # no clashes executed if for loop doesnt  break
                room = Room.objects.get(id__exact=roomId)
                b = Booking.objects.create(user=request.user, Room=room, booking_date=date, start_timing=start, end_timing=end, purpose_of_booking=purpose, is_pending=True)
                return Response("Booking has been added to the queue", status=status.HTTP_202_ACCEPTED)
        except:
            return Response({"message": "Invalid/Bad request"}, status=status.HTTP_400_BAD_REQUEST)


# User Details Related Views
class UserAccountInfo(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):
        total, accepted, pending, declined = 0, 0, 0, 0
        try:
            for obj in Booking.objects.filter(user=request.user):
                total += 1
                if obj.admin_did_accept:
                    accepted += 1
                elif obj.is_pending:
                    pending += 1
                else:
                    declined += 1
            res = {
                "id": request.user.id,
                "email": request.user.email,
                "name": request.user.name,
                "type": request.user.user_type,
                "total": total,
                "accepted": accepted,
                "pending": pending,
                "declined": declined,
            }
            return Response(res)
        except:
            return Response({"message": "Invalid/bad request"}, status=status.HTTP_400_BAD_REQUEST)


class UserPastBookingsView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):
        # currTime = datetime.datetime.now()
        # filterTime = int((currTime.hour + (currTime.minute / 60) - 7.5) * 2)
        res = []
        for item in Booking.objects.filter(user__exact=request.user, booking_date__lte=datetime.date.today(), end_timing__lt=datetime.datetime.now().time()):
            x = {"booking_date": item.booking_date,
                 "start_timing": item.start_timing,
                 "end_timing": item.end_timing,
                 "admin_did_accept": item.admin_did_accept,
                 "is_pending": item.is_pending,
                 "purpose_of_booking": item.purpose_of_booking,
                 "admin_feedback": item.admin_feedback,
                 "room_number": item.Room.room_number,
                 "room_name": item.Room.room_name
                 }
            res.append(x)
        return Response(sorted(res, key=lambda i: i['start_timing']))


class UserFutureBookingsView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):
        # currTime = datetime.datetime.now()
        # filterTime = int((currTime.hour + (currTime.minute / 60) - 7.5) * 2)
        # userId = get_user_model().objects.get(email=request.user).id
        slot = Booking.objects.filter(user=request.user, booking_date__gte=datetime.date.today())
        res = []
        for item in slot.filter(booking_date__gt=datetime.date.today()).union(slot.filter(booking_date__exact=datetime.date.today(), end_timing__gte=datetime.datetime.now().time())):
            x = {"booking_date": item.booking_date,
                 "start_timing": item.start_timing,
                 "end_timing": item.end_timing,
                 "admin_did_accept": item.admin_did_accept,
                 "is_pending": item.is_pending,
                 "purpose_of_booking": item.purpose_of_booking,
                 "admin_feedback": item.admin_feedback,
                 "room_number": item.Room.room_number,
                 "room_name": item.Room.room_name
                 }
            res.append(x)
        return Response(sorted(res, key=lambda i: i['start_timing']))


# Admin Views
class AdminDashboardStats(APIView):
    
    permission_classes = [IsAdminUser]

    def get(self, request):

        rooms = Room.objects.all()
        bookings = Booking.objects.all()
        users = get_user_model().objects.all()
        
        count = {'users': users.count(), 'bookings': bookings.count(), 'rooms': rooms.count()}
        
        countSchool = {}
        for item in rooms.order_by('school').distinct('school').values_list('school', flat=True):
            countSchool[item] = bookings.filter(Room__school__exact=item).count()
        
        slots = {}
        for item in bookings.order_by('start_timing').distinct('start_timing').values_list('start_timing', flat=True):
            slots[str(item)] = bookings.filter(start_timing__exact=item).count()

        return Response([count, countSchool, slots])


class AdminRequestActionView(APIView):

    permission_classes = [IsAdminUser]

    def get(self, request):
        response = []
        for item in Booking.objects.filter(is_pending__exact=True):
            room = Room.objects.get(id=item.Room.id)
            x = {"id": item.id,
                 "booking_date": item.booking_date,
                 "start_timing": item.start_timing,
                 "end_timing": item.end_timing,
                 "admin_did_accept": item.admin_did_accept,
                 "is_pending": item.is_pending,
                 "purpose_of_booking": item.purpose_of_booking,
                 "user": get_user_model().objects.get(email=item.user).email,
                 "room_id": room.id,
                 "room_name": room.room_name,
                 "room_number": room.room_number}
            response.append(x)
        return Response(response)

    def post(self, request):
        parser_classes = [JSONParser]
        try:
            res, data = [], request.data
            try:
                defaultMessage = data["message"]
            except:
                defaultMessage = "This request was automatically declined because it clashed with another request that was accepted. Any inconvenience is regretted."
            try:
                feedback = data["admin_feedback"]
            except:
                feedback = "Admin has not given any feedback"
            slot = Booking.objects.get(id=data["id"])
            if (data["admin_did_accept"] == False):
                slot.admin_did_accept = False
                slot.is_pending = False
                slot.admin_feedback = feedback
                slot.save()
            elif (data["admin_did_accept"] == True):
                slot.admin_did_accept = True
                slot.is_pending = False
                slot.admin_feedback = feedback
                slot.save()
                initialSlots = Booking.objects.filter(
                    booking_date__exact=slot.booking_date, Room=slot.Room).exclude(id=slot.id)
                rejectSlots = (initialSlots.filter(start_timing__gt=slot.end_timing)
                               | initialSlots.filter(end_timing__lt=slot.start_timing))
                finalSlots = initialSlots.exclude(id__in=rejectSlots).update(
                    admin_did_accept=False, is_pending=False, admin_feedback=defaultMessage)
            return Response({"message": "Action Completed"}, status=status.HTTP_200_OK)
        except:
            return Response({"message": "Invalid/Bad request"}, status=status.HTTP_400_BAD_REQUEST)


class BookingHistory(APIView):

    permission_classes = [IsAdminUser]

    def get(self, request):
        res = []
        for item in Booking.objects.all():
            x = {"id": item.id,
                 "user": item.user.email,
                 "room_name": item.Room.room_name,
                 "room_number": item.Room.room_number,
                 "booking_date": item.booking_date,
                 "start_timing": item.start_timing,
                 "end_timing": item.end_timing,
                 "admin_did_accept": item.admin_did_accept,
                 "is_pending": item.is_pending,
                 "purpose_of_booking": item.purpose_of_booking,
                 "admin_feedback": item.admin_feedback}
            res.append(x)
        return Response(res, status=status.HTTP_200_OK)
