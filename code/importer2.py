import os
import sys
import csv
import json
from random import randint
import time

# Django setup
sys.path.append(os.path.abspath(os.path.join(__file__, *[os.pardir] * 3)))
os.environ['DJANGO_SETTINGS_MODULE'] = 'simplelms.settings'
import django

django.setup()

from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from lms_core.models import Course, CourseMember, CourseContent, Comment

start_time = time.time()
filepath = './csv_data/'

# Log untuk mencatat data yang gagal diproses
invalid_log_path = 'invalid_data.log'

# Import Users
with open(filepath + 'user-data.csv') as csvfile:
    reader = csv.DictReader(csvfile)
    obj_create = []
    for row in reader:
        if not User.objects.filter(username=row['username']).exists():
            obj_create.append(User(
                username=row['username'],
                password=make_password(row['password']),
                email=row['email'],
                first_name=row['firstname'],
                last_name=row['lastname']
            ))
    User.objects.bulk_create(obj_create)

# Import Courses
with open(filepath + 'course-data.csv') as csvfile:
    reader = csv.DictReader(csvfile)
    obj_create = []
    for row in reader:
        if not Course.objects.filter(name=row['name']).exists():
            try:
                teacher = User.objects.get(pk=int(row['teacher']))
                obj_create.append(Course(
                    name=row['name'],
                    price=row['price'],
                    description=row['description'],
                    teacher=teacher
                ))
            except User.DoesNotExist:
                with open(invalid_log_path, 'a') as log_file:
                    log_file.write(f"Invalid Teacher ID for course: {row}\n")
    Course.objects.bulk_create(obj_create)

# Import Course Members
with open(filepath + 'member-data.csv') as csvfile:
    reader = csv.DictReader(csvfile)
    obj_create = []
    
    # Ambil semua pasangan yang sudah ada di database
    existing_pairs = set(CourseMember.objects.values_list('course_id', 'user_id'))
    
    for row in reader:
        course_id = int(row['course_id'])
        user_id = int(row['user_id'])
        pair = (course_id, user_id)
        
        # Pastikan pasangan tidak ada sebelum ditambahkan
        if pair not in existing_pairs:
            try:
                course = Course.objects.get(pk=course_id)
                user = User.objects.get(pk=user_id)
                obj_create.append(CourseMember(
                    course_id=course,
                    user_id=user,
                    roles=row['roles']
                ))
                
                # Tambahkan pasangan ke existing_pairs untuk menghindari duplikasi lebih lanjut
                existing_pairs.add(pair)
            except Course.DoesNotExist:
                with open(invalid_log_path, 'a') as log_file:
                    log_file.write(f"Invalid Course ID for member: {row}\n")
            except User.DoesNotExist:
                with open(invalid_log_path, 'a') as log_file:
                    log_file.write(f"Invalid User ID for member: {row}\n")

    # Simpan data yang valid ke dalam database
    CourseMember.objects.bulk_create(obj_create)


# Import Course Content
with open(filepath + 'contents.json') as jsonfile:
    contents = json.load(jsonfile)
    obj_create = []
    for row in contents:
        try:
            course = Course.objects.get(pk=int(row['course_id']))
            obj_create.append(CourseContent(
                course_id=course,
                name=row['name'],
                description=row['description']
            ))
        except Course.DoesNotExist:
            with open(invalid_log_path, 'a') as log_file:
                log_file.write(f"Invalid Course ID for content: {row}\n")

    CourseContent.objects.bulk_create(obj_create)

# Import Comments
with open(filepath + 'comments.json') as jsonfile:
    comments = json.load(jsonfile)
    obj_create = []
    with open('missing_course_members.log', 'w') as log_file:  # Log missing course members
        for row in comments:
            if int(row['user_id']) > 50:
                row['user_id'] = randint(5, 40)

            try:
                user = User.objects.get(pk=int(row['user_id']))
                course_content = CourseContent.objects.get(pk=int(row['content_id']))
                course_member = CourseMember.objects.filter(user_id=user, course_id=course_content.course_id).first()

                if not course_member:
                    log_file.write(f"user_id={row['user_id']}, course_id={course_content.course_id}\n")
                    continue

                if not Comment.objects.filter(content_id=course_content, member_id=course_member).exists():
                    obj_create.append(Comment(
                        content_id=course_content,
                        member_id=course_member,
                        comment=row['comment']
                    ))
            except User.DoesNotExist:
                with open(invalid_log_path, 'a') as log_file:
                    log_file.write(f"Invalid User ID for comment: {row}\n")
            except CourseContent.DoesNotExist:
                with open(invalid_log_path, 'a') as log_file:
                    log_file.write(f"Invalid Course Content ID for comment: {row}\n")

    Comment.objects.bulk_create(obj_create)

print("--- %s seconds ---" % (time.time() - start_time))