import json
import datetime

from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, JsonResponse
from django.shortcuts import (HttpResponseRedirect, get_object_or_404,redirect, render)
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from .forms import *
from .models import *



def staff_home(request):
    staff = get_object_or_404(Staff, admin=request.user)
    total_students = Student.objects.filter(dep=staff.dep).count()
    total_leave = LeaveReportStaff.objects.filter(staff=staff).count()
    courses = Course.objects.filter(staff=staff)
    total_course = courses.count()
    attendance_list = Attendance.objects.filter(course__in=courses)
    total_attendance = attendance_list.count()
    attendance_list = []
    course_list = []
    for course in courses:
        attendance_count = Attendance.objects.filter(course=course).count()
        course_list.append(course.name)
        attendance_list.append(attendance_count)
    context = {
        'page_title': 'Staff Panel - ' + str(staff.admin.last_name) + ' (' + str(staff.dep) + ')',
        'total_students': total_students,
        'total_attendance': total_attendance,
        'total_leave': total_leave,
        'total_course': total_course,
        'course_list': course_list,
        'attendance_list': attendance_list
    }
    return render(request, 'staff_template/home_content.html', context)


def staff_take_attendance(request):
    staff = get_object_or_404(Staff, admin=request.user)
    courses = Course.objects.filter(staff_id=staff)
    sessions = Session.objects.all()
    context = {
        'courses': courses,
        'sessions': sessions,
        'page_title': 'Take Attendance'
    }

    return render(request, 'staff_template/staff_take_attendance.html', context)


@csrf_exempt
def get_students(request):
    course_id = request.POST.get('course')
    session_id = request.POST.get('session')
    
    try:
        course = get_object_or_404(Course, id=course_id)
        session = get_object_or_404(Session, id=session_id)
        students = Student.objects.filter(
            dep_id=course.dep.id, session=session)
        student_data = []
        for student in students:
            data = {
                    "id": student.id,
                    "name": student.admin.last_name + " " + student.admin.first_name
                    }
            student_data.append(data)
        return JsonResponse(json.dumps(student_data), content_type='application/json', safe=False)
    except Exception as e:
        return e


@csrf_exempt
def save_attendance(request):
    student_data = request.POST.get('student_ids')
    date = request.POST.get('date')
    course_id = request.POST.get('course')
    session_id = request.POST.get('session')
    students = json.loads(student_data)
    try:
        session = get_object_or_404(Session, id=session_id)
        course = get_object_or_404(Course, id=course_id)
        attendance = Attendance(session=session, course=course, date=date)
        attendance.save()

        for student_dict in students:
            student = get_object_or_404(Student, id=student_dict.get('id'))
            attendance_report = AttendanceReport(student=student, attendance=attendance, status=student_dict.get('status'))
            attendance_report.save()
    except Exception as e:
        return None

    return HttpResponse("OK")


def staff_update_attendance(request):
    staff = get_object_or_404(Staff, admin=request.user)
    courses = Course.objects.filter(staff_id=staff)
    sessions = Session.objects.all()
    context = {
        'courses': courses,
        'sessions': sessions,
        'page_title': 'Update Attendance'
    }

    return render(request, 'staff_template/staff_update_attendance.html', context)


@csrf_exempt
def get_student_attendance(request):
    attendance_date_id = request.POST.get('attendance_date_id')
    try:
        date = get_object_or_404(Attendance, id=attendance_date_id)
        attendance_data = AttendanceReport.objects.filter(attendance=date)
        student_data = []
        for attendance in attendance_data:
            data = {"id": attendance.student.id,
                    "name": attendance.student.admin.last_name + " " + attendance.student.admin.first_name,
                    "status": attendance.status}
            student_data.append(data)
        return JsonResponse(json.dumps(student_data), content_type='application/json', safe=False)
    except Exception as e:
        return e


@csrf_exempt
def update_attendance(request):
    print(f' FUNCTION CALLED{"*" * 10}')
    student_data = request.POST.get('student_ids')
    date = request.POST.get('date')
    print(f'data: {date}')
    students = json.loads(student_data)
    print(f'students: {students}')
    try:
        attendance = get_object_or_404(Attendance, id=date)

        for student_dict in students:
            student = get_object_or_404(
                Student, admin_id=student_dict.get('id'))
            attendance_report = get_object_or_404(AttendanceReport, student=student, attendance=attendance)
            attendance_report.status = student_dict.get('status')
            attendance_report.save()
            print(f'student_dict: {student_dict}')
    except Exception as e:
        return None

    return HttpResponse("OK")

def assignments(request):
    page_title = 'Assignments'
    staff = get_object_or_404(Staff, admin_id=request.user.id)
    assignments = Assignment.objects.filter(staff=staff)
    total_assignments = assignments.count()
    assignments_list = []
    
    for assignment in assignments:
        session = assignment.session
        students = Student.objects.filter(session=session).count()
        submissions = Submission.objects.filter(assignment=assignment).count()
        percentage_submit = f'{submissions/students * 100}%'
        
        assignments_list.append({
            'id': assignment.id,
            'course': assignment.course,
            'title': assignment.title,
            'due_date': assignment.due_date,
            'submissions': submissions,
            'percentage_submit': percentage_submit
        })
        
    context = {
        'page_title': page_title,
        'assignments_list': assignments,
        'total_assignments': total_assignments
    }
    
    return render(request, 'staff_template/assignments.html', context)

def upload_assignment(request):
    page_title = 'Upload Assignment'
    
    if request.method == 'POST':
        form = AssignmentForm(request.POST, request.FILES)
        if form.is_valid():
            staff = get_object_or_404(Staff, admin_id=request.user.id)
            obj = form.save(commit=False)
            obj.staff = staff
            obj.save()
            messages.success(
                    request, f"Assignment {request.POST.get('title')} was successfully uploaded")
            return redirect('assignments')
    else:
        form = AssignmentForm()
        
    context = {
        'form': form,
        'page_title': page_title
    }
    
    return render(request, 'staff_template/upload_assignment.html', context)

def staff_submissions(request, ass_pk):
    page_title = 'Assignment Grading'
    assignment = get_object_or_404(Assignment, id=ass_pk)
    session = get_object_or_404(Session, id=assignment.session.id)
    total_course_students = Student.objects.filter(session=session).count()
    submissions = Submission.objects.filter(assignment=assignment)
    total_submits = submissions.count()
    percentage_submit = total_submits * 100 / total_course_students
    
    context = {
        'submissions': submissions,
        'total_submits': total_submits,
        'percentage_submit': percentage_submit,
        'total_course_students': total_course_students,
        'assignment': assignment
    }
    
    return render(request, 'staff_template/staff_submissions.html', context)

def grade_assignment(request, pk):
    submission = get_object_or_404(Submission, id=pk)
    
    if request.method == 'POST':
        staff = get_object_or_404(Staff, admin_id=request.user.id)
        grade = float(request.POST.get('grade'))
        
        submission.grade = grade
        submission.graded_by = staff
        submission.save()
        messages.success(
                    request, f"{submission.student}'s Assignment was successfully graded")
        return redirect(reverse('staff_submissions', args=(submission.assignment.id,)))
    
    page_title = f'Grade {submission.student}'
    context = {
        'page_title': page_title,
        'submission': submission,
    }
    
    return render(request, 'staff_template/grade_assignment.html', context)

def course_materials(request):
    page_title = 'Course Materials'
    
    staff = get_object_or_404(Staff, admin_id=request.user.id)
    courses = Course.objects.filter(staff=staff)
    materials = []
    
    for course in courses:
        material = CourseMaterial.objects.filter(course=course).count()
        materials.append({
            'id': course.id,
            'course': course,
            'materials': material
        })
    
    context = {
        'page_title': page_title,
        'materials': materials,
        # 'total_materials': total_materials
    }
    
    return render(request, 'staff_template/course_materials.html', context)

def view_materials(request, pk):
    course = get_object_or_404(Course, id=pk)
    materials = CourseMaterial.objects.filter(course=course)
    page_title = f'{course} Materials'
    
    context = {
        'page_title': page_title,
        'course': course,
        'materials': materials
    }
    
    return render(request, 'staff_template/view_materials.html', context)

def upload_material(request):
    page_title = 'Upload Course Material'
    
    if request.method == 'POST':
        form = CourseMaterialForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(
                    request, f"Course Material for {request.POST.get('name')} was successfully uploaded")
            return redirect(reverse('course_materials'))
    else:
        form = CourseMaterialForm()
    
    context = {
        'page_title': page_title,
        'form': form
    }
    return render(request, 'staff_template/upload_material.html', context)

def staff_apply_leave(request):
    form = LeaveReportStaffForm(request.POST or None)
    staff = get_object_or_404(Staff, admin_id=request.user.id)
    context = {
        'form': form,
        'leave_history': LeaveReportStaff.objects.filter(staff=staff),
        'page_title': 'Apply for Leave'
    }
    if request.method == 'POST':
        if form.is_valid():
            try:
                obj = form.save(commit=False)
                obj.staff = staff
                obj.save()
                messages.success(
                    request, "Application for leave has been submitted for review")
                return redirect(reverse('staff_apply_leave'))
            except Exception:
                messages.error(request, "Could not apply!")
        else:
            messages.error(request, "Form has errors!")
    return render(request, "staff_template/staff_apply_leave.html", context)

def staff_feedback(request):
    form = FeedbackStaffForm(request.POST or None)
    staff = get_object_or_404(Staff, admin_id=request.user.id)
    context = {
        'form': form,
        'feedbacks': FeedbackStaff.objects.filter(staff=staff),
        'page_title': 'Add Feedback'
    }
    if request.method == 'POST':
        if form.is_valid():
            try:
                obj = form.save(commit=False)
                obj.staff = staff
                obj.save()
                messages.success(request, "Feedback submitted for review")
                return redirect(reverse('staff_feedback'))
            except Exception:
                messages.error(request, "Could not Submit!")
        else:
            messages.error(request, "Form has errors!")
    return render(request, "staff_template/staff_feedback.html", context)


def staff_view_profile(request):
    staff = get_object_or_404(Staff, admin=request.user)
    form = StaffEditForm(request.POST or None, request.FILES or None,instance=staff)
    context = {'form': form, 'page_title': 'View/Update Profile'}
    if request.method == 'POST':
        try:
            if form.is_valid():
                first_name = form.cleaned_data.get('first_name')
                last_name = form.cleaned_data.get('last_name')
                password = form.cleaned_data.get('password') or None
                address = form.cleaned_data.get('address')
                gender = form.cleaned_data.get('gender')
                passport = request.FILES.get('profile_pic') or None
                admin = staff.admin
                if password != None:
                    admin.set_password(password)
                if passport != None:
                    fs = FileSystemStorage()
                    filename = fs.save(passport.name, passport)
                    passport_url = fs.url(filename)
                    admin.profile_pic = passport_url
                admin.first_name = first_name
                admin.last_name = last_name
                admin.address = address
                admin.gender = gender
                admin.save()
                staff.save()
                messages.success(request, "Profile Updated!")
                return redirect(reverse('staff_view_profile'))
            else:
                messages.error(request, "Invalid Data Provided")
                return render(request, "staff_template/staff_view_profile.html", context)
        except Exception as e:
            messages.error(
                request, "Error Occured While Updating Profile " + str(e))
            return render(request, "staff_template/staff_view_profile.html", context)

    return render(request, "staff_template/staff_view_profile.html", context)


@csrf_exempt
def staff_fcmtoken(request):
    token = request.POST.get('token')
    try:
        staff_user = get_object_or_404(CustomUser, id=request.user.id)
        staff_user.fcm_token = token
        staff_user.save()
        return HttpResponse("True")
    except Exception as e:
        return HttpResponse("False")


def staff_view_notification(request):
    staff = get_object_or_404(Staff, admin=request.user)
    notifications = NotificationStaff.objects.filter(staff=staff)
    context = {
        'notifications': notifications,
        'page_title': "View Notifications"
    }
    return render(request, "staff_template/staff_view_notification.html", context)


def staff_add_result(request):
    staff = get_object_or_404(Staff, admin=request.user)
    courses = Course.objects.filter(staff=staff)
    sessions = Session.objects.all()
    context = {
        'page_title': 'Result Upload',
        'courses': courses,
        'sessions': sessions
    }
    if request.method == 'POST':
        try:
            student_id = request.POST.get('student_list')
            course_id = request.POST.get('course')
            test = request.POST.get('test')
            exam = request.POST.get('exam')
            student = get_object_or_404(Student, id=student_id)
            course = get_object_or_404(Course, id=course_id)
            try:
                data = StudentResult.objects.get(
                    student=student, course=course)
                data.exam = exam
                data.test = test
                data.save()
                messages.success(request, "Scores Updated")
            except:
                result = StudentResult(student=student, course=course, test=test, exam=exam)
                result.save()
                messages.success(request, "Scores Saved")
        except Exception as e:
            messages.warning(request, "Error Occured While Processing Form")
    return render(request, "staff_template/staff_add_result.html", context)


@csrf_exempt
def fetch_student_result(request):
    try:
        course_id = request.POST.get('course')
        student_id = request.POST.get('student')
        student = get_object_or_404(Student, id=student_id)
        course = get_object_or_404(Course, id=course_id)
        result = StudentResult.objects.get(student=student, course=course)
        result_data = {
            'exam': result.exam,
            'test': result.test
        }
        return HttpResponse(json.dumps(result_data))
    except Exception as e:
        return HttpResponse('False')
