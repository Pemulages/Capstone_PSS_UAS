from django import forms
from django.contrib import admin
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
from lms_core.models import Category, Course, CourseMember, CourseContent, Comment, Announcement, CourseCompletion, ContentCompletion
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.decorators import user_passes_test

class BatchEnrollForm(forms.Form):
    course = forms.ModelChoiceField(queryset=Course.objects.all(), label="Course")
    students = forms.ModelMultipleChoiceField(queryset=User.objects.filter(is_staff=False), label="Students")

def batch_enroll(request):
    if request.method == 'POST':
        form = BatchEnrollForm(request.POST)
        if form.is_valid():
            course = form.cleaned_data['course']
            students = form.cleaned_data['students']
            for student in students:
                CourseMember.objects.get_or_create(course_id=course, user_id=student)
            messages.success(request, "Students enrolled successfully")
            return redirect('admin:index')
    else:
        form = BatchEnrollForm()
    return render(request, 'admin/batch_enroll.html', {'form': form})

class MyAdminSite(admin.AdminSite):
    site_header = 'LMS Administration'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('batch_enroll/', self.admin_view(batch_enroll), name='batch_enroll'),
        ]
        return custom_urls + urls

admin_site = MyAdminSite(name='myadmin')

# Course Admin
@admin.register(Course, site=admin_site)
class CourseAdmin(admin.ModelAdmin):
    list_display = ["name", "price", "description", "teacher", "category", "created_at"]
    list_filter = ["teacher", "category"]
    search_fields = ["name", "description", "teacher__username", "category__name"]
    readonly_fields = ["created_at", "updated_at"]
    fields = ["name", "description", "price", "image", "teacher", "category", "created_at", "updated_at"]

# CourseMember Admin
@admin.register(CourseMember, site=admin_site)
class CourseMemberAdmin(admin.ModelAdmin):
    list_display = ["course_name", "user_name", "roles", "created_at"]
    list_filter = ["course_id", "user_id", "roles"]
    search_fields = ["course_id__name", "user_id__username"]
    readonly_fields = ["created_at", "updated_at"]
    fields = ["course_id", "user_id", "roles", "created_at", "updated_at"]

    def course_name(self, obj):
        return obj.course_id.name
    course_name.admin_order_field = 'course_id__name'

    def user_name(self, obj):
        return obj.user_id.username
    user_name.admin_order_field = 'user_id__username'

# CourseContent Admin
@admin.register(CourseContent, site=admin_site)
class CourseContentAdmin(admin.ModelAdmin):
    list_display = ["name", "course_name", "scheduled_start_time", "scheduled_end_time", "created_at"]
    list_filter = ["course_id"]
    search_fields = ["name", "course_id__name"]
    readonly_fields = ["created_at", "updated_at"]
    fields = ["name", "description", "file_attachment", "course_id", "parent_id", "scheduled_start_time", "scheduled_end_time", "created_at", "updated_at"]

    def course_name(self, obj):
        return obj.course_id.name
    course_name.admin_order_field = 'course_id__name'

# Comment Admin
@admin.register(Comment, site=admin_site)
class CommentAdmin(admin.ModelAdmin):
    list_display = ["content_name", "user_name", "comment", "is_approved", "created_at"]
    list_filter = ["is_approved"]
    search_fields = ["content_id__name", "member_id__user_id__username"]
    readonly_fields = ["created_at", "updated_at"]
    fields = ["content_id", "member_id", "comment", "is_approved", "created_at", "updated_at"]

    def content_name(self, obj):
        return obj.content_id.name
    content_name.admin_order_field = 'content_id__name'

    def user_name(self, obj):
        return obj.member_id.user_id.username
    user_name.admin_order_field = 'member_id__user_id__username'

# Register custom admin site
admin.site = admin_site

# Custom User Admin
class CustomUserAdmin(BaseUserAdmin):
    add_form = UserCreationForm
    form = UserChangeForm
    model = User
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff']
    list_filter = ['is_staff', 'is_superuser', 'is_active']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering = ['username']
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'email', 'first_name', 'last_name', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
    )

# Register Custom User Admin
admin_site.register(User, CustomUserAdmin)

# Announcement Admin
class AnnouncementAdminForm(forms.ModelForm):
    class Meta:
        model = Announcement
        exclude = ['created_by'] 
        
@admin.register(Announcement, site=admin_site)
class AnnouncementAdmin(admin.ModelAdmin):
    form = AnnouncementAdminForm
    list_display = ['title', 'course_name', 'start_date', 'end_date', 'created_by', 'created_at']
    list_filter = ['course_id', 'created_by']
    search_fields = ['title', 'content', 'course_id__name', 'created_by__username']
    readonly_fields = ['created_at', 'updated_at']
    fields = ['title', 'content', 'start_date', 'end_date', 'course', 'created_at', 'updated_at']

    def course_name(self, obj):
        return obj.course.name
    course_name.admin_order_field = 'course_id__name'

    def save_model(self, request, obj, form, change):
        if not obj.created_by:
            obj.created_by = request.user
        obj.save()
        
# Category Admin
class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if len(name) > 255:
            raise forms.ValidationError("Nama kategori tidak boleh lebih dari 255 karakter.")
        return name

@admin.register(Category, site=admin_site)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_by', 'created_at']
    readonly_fields = ['created_at']
    exclude = ['created_by']

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

# CourseCompletion Admin
class CourseCompletionAdmin(admin.ModelAdmin):
    list_display = ("user", "course", "completed_at", "certificate_link")
    list_filter = ("user", "course")
    search_fields = ("user__username", "course__name")
    readonly_fields = ("completed_at",)

    def certificate_link(self, obj):
        from django.utils.html import format_html
        url = f"/certificate/{obj.user.id}/{obj.course.id}/"
        return format_html('<a class="button" href="{}" target="_blank">Lihat Sertifikat</a>', url)
    certificate_link.short_description = "Sertifikat"

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # Otomatis isi ContentCompletion untuk semua konten course
        contents = CourseContent.objects.filter(course_id=obj.course)
        for content in contents:
            ContentCompletion.objects.get_or_create(user=obj.user, content=content)

admin_site.register(CourseCompletion, CourseCompletionAdmin)

class ContentCompletionAdmin(admin.ModelAdmin):
    list_display = ("user", "content", "completed_at")
    list_filter = ("user", "content")
    search_fields = ("user__username", "content__name")

admin_site.register(ContentCompletion, ContentCompletionAdmin)