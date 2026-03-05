from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from todo.models import Computer, Reservation
from datetime import datetime, timedelta
import json

# ---------------- PC Login Page ----------------
def pc_login_page(request):
    # Reserved seats to show in datalist
    reserved_seats = Reservation.objects.filter(
        status__in=["Pending", "SUCCESS", "Active", "Confirmed"]
    ).values_list('seat', flat=True).distinct()

    return render(request, "pc_login/pc_login.html", {"reserved_seats": reserved_seats})

# ---------------- PC Login API ----------------
@csrf_exempt
def pc_login_api(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Invalid request method."})

    try:
        data = json.loads(request.body)
        username = data.get("username")
        password = data.get("password")
        pc_input = data.get("pc_id")

        if not username or not password or not pc_input:
            return JsonResponse({"success": False, "error": "Please fill all fields."})

        # Authenticate user
        user = authenticate(username=username, password=password)
        if not user:
            return JsonResponse({"success": False, "error": "Invalid username or password."})

        # Normalize PC input
        pc_clean = pc_input.replace("-", "").replace(" ", "").upper()

        # Get Computer
        try:
            pc = Computer.objects.get(pc_id__iexact=pc_clean)
        except Computer.DoesNotExist:
            return JsonResponse({"success": False, "error": f"PC {pc_input} not found!"})

        if pc.status == "In Use":
            return JsonResponse({"success": False, "error": "PC already in use!"})

        # Normalize seat check for Reservation
        def normalize_seat(seat):
            return seat.replace("-", "").replace(" ", "").upper()

        reservation = None
        for r in Reservation.objects.filter(user=user, status__in=["Pending", "SUCCESS", "Active", "Confirmed"]):
            if normalize_seat(r.seat) == pc_clean:
                reservation = r
                break

        if not reservation:
            return JsonResponse({"success": False, "error": f"No reservation for {pc_input}!"})

        # ✅ Update PC status and assign current user
        pc.status = "In Use"
        pc.current_user = user
        pc.save()

        # ✅ Update reservation status
        reservation.status = "Active"
        reservation.save()

        # Login user
        login(request, user)

        return JsonResponse({
            "success": True,
            "message": f"PC {pc.pc_id} logged in successfully!",
            "redirect_url": "/pc/dashboard/"
        })

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})

# ---------------- PC Dashboard ----------------
@login_required
def pc_dashboard(request):
    # I-check kung may PC naka-assign sa user at active
    pc = Computer.objects.filter(current_user=request.user, status="In Use").first()

    if not pc:
        # Walang naka-assign → pwede rin natin i-check reservation
        reservation = Reservation.objects.filter(user=request.user, status="Active").first()
        if reservation:
            try:
                pc = Computer.objects.get(pc_id__iexact=reservation.seat)
                # Update PC current_user para siguradong match
                pc.current_user = request.user
                pc.status = "In Use"
                pc.save()
            except Computer.DoesNotExist:
                # Walang PC → balik login
                return redirect('pc_login')
        else:
            return redirect('pc_login')

    # PCs sa same room
    room_pcs = Computer.objects.filter(room=pc.room)

    session_end = datetime.now() + timedelta(hours=2)
    session = {"end_time": session_end}

    return render(request, "pc_login/pc_dashboard.html", {
        "pc": pc,
        "room_pcs": room_pcs,
        "session": session
    })