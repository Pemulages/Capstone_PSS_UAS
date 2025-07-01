import json
from sqlite3 import IntegrityError
from django.shortcuts import render, HttpResponse, redirect, get_object_or_404
from django.http import JsonResponse
from django.core.exceptions import ObjectDoesNotExist,ValidationError
from django.core import serializers
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import user_passes_test
from django import forms

from lms_core.models import Course, Comment, CourseContent, CourseMember, Announcement, Category, ContentCompletion

def index(request):
    return HttpResponse("<h1>Hello World Simple LMS</h1>")

def testing(request):
    dataCourse = Course.objects.all()
    dataCourse = serializers.serialize("python", dataCourse)
    return JsonResponse(dataCourse, safe=False)

def addData(request): 
    course = Course(
        name = "Belajar Django",
        description = "Belajar Django dengan Mudah",
        price = 1000000,
        teacher = User.objects.get(username="masahiro")
    )
    course.save()
    return JsonResponse({"message": "Data berhasil ditambahkan"})

def editData(request):
    course = Course.objects.filter(name="Belajar Django").first()
    course.name = "Belajar Django Setelah update"
    course.save()
    return JsonResponse({"message": "Data berhasil diubah"})

def deleteData(request):
    course = Course.objects.filter(name__icontains="Belajar Django").first()
    course.delete()
    return JsonResponse({"message": "Data berhasil dihapus"})

@csrf_exempt
def register(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get("username")
            password = data.get("password")
            email = data.get("email")

            if not username or not password or not email:
                return JsonResponse({"error": "All fields are required"}, status=400)

            if User.objects.filter(username=username).exists():
                return JsonResponse({"error": "Username already exists"}, status=400)

            User.objects.create_user(username=username, password=password, email=email)
            return JsonResponse({"message": "User registered successfully"}, status=201)
        
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data"}, status=400)

    return JsonResponse({"error": "Invalid request method"}, status=405)

def list_comments(request, content_id):
    comments = Comment.objects.filter(content_id=content_id, is_approved=True)
    
    if not comments.exists():
        return JsonResponse({"message": "No approved comments found for this content."}, status=404)
    
    data = serializers.serialize("json", comments)
    return JsonResponse(data, safe=False)

@csrf_exempt
def moderate_comment(request, content_id, comment_id):
    comment = get_object_or_404(Comment, id=comment_id, content_id=content_id)

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            is_approved = data.get('is_approved')

            if is_approved is None:
                return JsonResponse({"error": "is_approved field is required"}, status=400)

            comment.is_approved = is_approved
            comment.save()
            return JsonResponse({"message": "Comment updated successfully"}, status=200)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data"}, status=400)

    return JsonResponse({"error": "Invalid request method"}, status=405)

def user_activity_dashboard(request, user_id):
    user = get_object_or_404(User, id=user_id)
    stats = user.get_course_stats()
    return JsonResponse(stats)

def course_analytics(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    stats = course.get_course_stats()
    return JsonResponse(stats)

def list_course_contents(request, course_id):
    contents = CourseContent.objects.filter(course_id=course_id, scheduled_start_time__lte=timezone.now())
    
    data = [
        {
            "id": content.id,
            "name": content.name,
            "description": content.description,
            "scheduled_start_time": content.scheduled_start_time,
            "scheduled_end_time": content.scheduled_end_time,
            "is_available": content.is_available(),  
            "course": {
                "id": content.course_id.id,
                "name": content.course_id.name,
            },
        }
        for content in contents
    ]
    
    return JsonResponse(data, safe=False)

class BatchEnrollForm(forms.Form):
    course = forms.ModelChoiceField(queryset=Course.objects.all(), label="Course")
    students = forms.ModelMultipleChoiceField(queryset=User.objects.filter(is_staff=False), label="Students")

def batch_enroll(request):
    if request.method == 'POST':
        form = BatchEnrollForm(request.POST)
        if form.is_valid():
            course = form.cleaned_data['course']
            students = form.cleaned_data['students']
            if CourseMember.objects.filter(course_id=course).count() + len(students) > course.max_students:
                messages.error(request, "Not enough slots available for all students")
                return redirect('batch_enroll')
            for student in students:
                if not CourseMember.objects.filter(course_id=course, user_id=student).exists():
                    CourseMember.objects.create(course_id=course, user_id=student)
            messages.success(request, "Students enrolled successfully")
            return redirect('admin:index')
    else:
        form = BatchEnrollForm()
    return render(request, 'admin/batch_enroll.html', {'form': form})

@csrf_exempt
def enroll_student(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            course_id = data.get('course_id')
            user_id = data.get('user_id')

            if not course_id or not user_id:
                return JsonResponse({"error": "Missing course_id or user_id"}, status=400)

            try:
                course = Course.objects.get(id=course_id)
            except ObjectDoesNotExist:
                return JsonResponse({"error": f"Course with id {course_id} does not exist"}, status=404)

            try:
                user = User.objects.get(id=user_id)
            except ObjectDoesNotExist:
                return JsonResponse({"error": f"User with id {user_id} does not exist"}, status=404)

            if CourseMember.objects.filter(course_id=course, user_id=user).exists():
                return JsonResponse({"error": "Student is already enrolled in this course"}, status=400)

            max_students = course.max_students
            if max_students is not None: 
                enrolled_count = CourseMember.objects.filter(course_id=course).count()
                if enrolled_count >= max_students:
                    return JsonResponse({"error": "Course is full"}, status=400)

            CourseMember.objects.create(course_id=course, user_id=user)
            return JsonResponse({"message": "Student enrolled successfully"}, status=201)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data"}, status=400)
        
        except IntegrityError as e:
            return JsonResponse({"error": f"Database error: {str(e)}"}, status=500)
        
    return JsonResponse({"error": "Invalid request method"}, status=405)

@csrf_exempt
def create_announcement(request, course_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            title = data.get('title')
            content = data.get('content')
            start_date = data.get('start_date')
            end_date = data.get('end_date')
            
            if not title or not content or not start_date or not end_date:
                return JsonResponse({"error": "All fields are required"}, status=400)

            user = request.user
            course = get_object_or_404(Course, id=course_id)
            if user != course.teacher:
                return JsonResponse({"error": "Only the course teacher can create announcements"}, status=403)

            announcement = Announcement.objects.create(
                course=course,
                title=title,
                content=content,
                start_date=start_date,
                end_date=end_date,
                created_by=user
            )
            return JsonResponse({"message": "Announcement created successfully", "id": announcement.id}, status=201)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data"}, status=400)
    return JsonResponse({"error": "Invalid request method"}, status=405)

def show_announcements(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    announcements = Announcement.objects.filter(course=course)
    active_announcements = [
        {
            "id": announcement.id,
            "title": announcement.title,
            "content": announcement.content,
            "start_date": announcement.start_date,
            "end_date": announcement.end_date,
            "is_active": announcement.is_active(),
        }
        for announcement in announcements if announcement.is_active()
    ]
    return JsonResponse(active_announcements, safe=False)

@csrf_exempt
def edit_announcement(request, announcement_id):
    try:
        announcement = get_object_or_404(Announcement, id=announcement_id)
    except Announcement.DoesNotExist:
        return JsonResponse({"error": "Announcement not found"}, status=404)

    if request.user != announcement.created_by:
        return JsonResponse({"error": "Only the course teacher can edit announcements"}, status=403)

    if request.method == 'PUT':
        try:
            data = json.loads(request.body)
            title = data.get('title')
            content = data.get('content')
            start_date = data.get('start_date')
            end_date = data.get('end_date')

            if not title or not content or not start_date or not end_date:
                return JsonResponse({"error": "All fields are required"}, status=400)

            announcement.title = title
            announcement.content = content
            announcement.start_date = start_date
            announcement.end_date = end_date
            announcement.save()

            return JsonResponse({"message": "Announcement updated successfully"}, status=200)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data"}, status=400)

    return JsonResponse({"error": "Invalid request method"}, status=405)

@csrf_exempt
def delete_announcement(request, announcement_id):
    try:
        announcement = get_object_or_404(Announcement, id=announcement_id)
    except Announcement.DoesNotExist:
        return JsonResponse({"error": "Announcement not found"}, status=404)

    if request.user != announcement.created_by:
        return JsonResponse({"error": "Only the course teacher can delete announcements"}, status=403)

    if request.method == 'DELETE':
        announcement.delete()
        return JsonResponse({"message": "Announcement deleted successfully"}, status=200)

    return JsonResponse({"error": "Invalid request method"}, status=405)

@csrf_exempt
def create_category(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            name = data.get('name')

            if not name:
                return JsonResponse({"error": "Category name is required"}, status=400)

            category = Category.objects.create(
                name=name,
                created_by=request.user if request.user.is_authenticated else None
            )

            return JsonResponse({"message": "Category created successfully", "id": category.id}, status=201)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data"}, status=400)
    return JsonResponse({"error": "Invalid request method"}, status=405)

def show_category(request):
    categories = Category.objects.all()
    data = [
        {
            "id": category.id,
            "name": category.name,
            "created_by": category.created_by.username,
            "created_at": category.created_at,
        } for category in categories
    ]
    return JsonResponse(data, safe=False)

@csrf_exempt
def delete_category(request, category_id):
    try:
        category = get_object_or_404(Category, id=category_id, created_by=request.user)
    except Category.DoesNotExist:
        return JsonResponse({"error": "Category not found"}, status=404)

    if request.method == 'DELETE':
        category.delete()
        return JsonResponse({"message": "Category deleted successfully"}, status=200)

    return JsonResponse({"error": "Invalid request method"}, status=405)

def course_certificate(request, user_id, course_id):
    user = get_object_or_404(User, id=user_id)
    course = get_object_or_404(Course, id=course_id)
    contents = CourseContent.objects.filter(course_id=course)
    total_contents = contents.count()
    completed_count = ContentCompletion.objects.filter(user=user, content__in=contents).count()

    if total_contents == 0 or completed_count < total_contents:
        return HttpResponse("<h2>Sertifikat hanya tersedia jika semua konten kursus telah diselesaikan.</h2>")

    # Ambil waktu penyelesaian terakhir
    last_completion = ContentCompletion.objects.filter(user=user, content__in=contents).order_by('-completed_at').first()
    completed_at = last_completion.completed_at if last_completion else timezone.now()

    return render(request, 'certificate/certificate.html', {
        'user': user,
        'course': course,
        'completed_at': completed_at,
    })

from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import user_passes_test
from django.http import JsonResponse
from django.contrib.auth.models import User
from .models import ContentCompletion, CourseContent

@csrf_exempt
@user_passes_test(lambda u: u.is_staff)
def mark_content_completed(request):
    if request.method == "POST":
        user_id = request.POST.get("user_id")
        content_id = request.POST.get("content_id")
        try:
            user = User.objects.get(id=user_id)
            content = CourseContent.objects.get(id=content_id)
            obj, created = ContentCompletion.objects.get_or_create(user=user, content=content)
            return JsonResponse({"success": True, "created": created})
        except User.DoesNotExist:
            return JsonResponse({"error": "User not found"}, status=404)
        except CourseContent.DoesNotExist:
            return JsonResponse({"error": "Content not found"}, status=404)
    return JsonResponse({"error": "Invalid request"}, status=400)
