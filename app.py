from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
import MySQLdb.cursors
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config.from_object(Config)

app.config["UPLOAD_FOLDER"] = "static/uploads"
app.config["ALLOWED_EXTENSIONS"] = {"png", "jpg", "jpeg", "gif", "pdf"}

if app.config.get("MYSQL_SSL_CA"):
    app.config["MYSQL_SSL"] = {"ca": app.config["MYSQL_SSL_CA"]}
    
mysql = MySQL(app)


from datetime import datetime

@app.route("/")
def home():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    cur.execute("SELECT COUNT(*) as total FROM projects")
    project_count = cur.fetchone()["total"]

    cur.execute("SELECT tech_stack FROM projects WHERE tech_stack IS NOT NULL")
    rows = cur.fetchall()
    tech_set = set()
    for row in rows:
        techs = row["tech_stack"].split(",")
        for t in techs:
            tech_set.add(t.strip())
    tech_count = len(tech_set)

    cur.execute("SELECT COUNT(*) as total FROM certifications")
    cert_count = cur.fetchone()["total"]

    cur.execute("SELECT COUNT(*) as total FROM certifications")
    cert_count = cur.fetchone()["total"]

    cur.execute("SELECT * FROM certifications ORDER BY created_at DESC")
    certifications = cur.fetchall()

    start_year = 2024
    current_year = datetime.now().year
    experience_years = current_year - start_year

    cur.execute("SELECT * FROM timeline WHERE category='experience' ORDER BY id DESC")
    experience = cur.fetchall()

    cur.execute("SELECT * FROM timeline WHERE category='education' ORDER BY id DESC")
    education = cur.fetchall()

    cur.close()

    return render_template(
        "home.html",
        project_count=project_count,
        tech_count=tech_count,
        experience_years=experience_years,
        cert_count=cert_count,
        certifications=certifications,
        experience=experience,
        education=education 
    )

@app.route("/add-certification", methods=["POST"])
def add_certification():
    if "admin" not in session:
        return redirect(url_for("login"))

    name = request.form["name"]
    org = request.form["organization"]
    link = request.form["link"]
    image = request.files.get("image")
    filename = None

    if image and allowed_file(image.filename):
        filename = secure_filename(image.filename)
        image.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

    cur = mysql.connection.cursor()
    cur.execute("""
        INSERT INTO certifications (name, issuing_organization, cert_link, image_name)
        VALUES (%s, %s, %s, %s)
    """, (name, org, link, filename))
    
    mysql.connection.commit()
    cur.close()

    flash("Certification added!", "success")
    return redirect(url_for("dashboard"))

@app.route("/projects")
def projects():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    cur.execute("SELECT * FROM projects ORDER BY created_at DESC")
    projects = cur.fetchall()

    for project in projects:
        cur.execute("SELECT image_name FROM project_images WHERE project_id=%s", (project["id"],))
        project["images"] = cur.fetchall()

    cur.close()

    return render_template("projects.html", projects=projects)

@app.route("/add-project", methods=["POST"])
def add_project():
    if "admin" not in session:
        return redirect(url_for("login"))

    title = request.form["title"]
    description = request.form["description"]
    tech_stack = request.form["tech_stack"]
    github_link = request.form["github_link"]
    live_link = request.form["live_link"]

    cur = mysql.connection.cursor()

    cur.execute("""
        INSERT INTO projects (title, description, tech_stack, github_link, live_link)
        VALUES (%s, %s, %s, %s, %s)
    """, (title, description, tech_stack, github_link, live_link))

    project_id = cur.lastrowid

    images = request.files.getlist("images")

    for image in images:
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

            cur.execute("""
                INSERT INTO project_images (project_id, image_name)
                VALUES (%s, %s)
            """, (project_id, filename))

    mysql.connection.commit()
    cur.close()

    flash("Project added with images!", "success")
    return redirect(url_for("dashboard"))

@app.route("/edit-project/<int:project_id>", methods=["GET", "POST"])
def edit_project(project_id):
    if "admin" not in session:
        return redirect(url_for("login"))

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        tech_stack = request.form["tech_stack"]
        github_link = request.form["github_link"]
        live_link = request.form["live_link"]

        cur.execute("""
            UPDATE projects
            SET title=%s, description=%s, tech_stack=%s,
                github_link=%s, live_link=%s
            WHERE id=%s
        """, (title, description, tech_stack,
              github_link, live_link, project_id))

        images = request.files.getlist("images")

        for image in images:
            if image and allowed_file(image.filename):
                filename = secure_filename(image.filename)
                image.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

                cur.execute("""
                    INSERT INTO project_images (project_id, image_name)
                    VALUES (%s, %s)
                """, (project_id, filename))

        mysql.connection.commit()
        cur.close()

        flash("Project updated successfully!", "success")
        return redirect(url_for("dashboard"))

    cur.execute("SELECT * FROM projects WHERE id=%s", (project_id,))
    project = cur.fetchone()

    cur.execute("SELECT image_name FROM project_images WHERE project_id=%s", (project_id,))
    project["images"] = cur.fetchall()

    cur.close()

    return render_template("edit_project.html", project=project)

@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        subject = request.form.get("subject", "") 
        message = request.form["message"]

        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute(
            """
            INSERT INTO messages (name, email, subject, message)
            VALUES (%s, %s, %s, %s)
            """,
            (name, email, subject, message),
        )
        mysql.connection.commit()
        cur.close()

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({"status": "success", "message": "Message sent successfully! I'll get back to you soon."})

        flash("Message sent successfully!", "success")
        return redirect(url_for("contact"))

    return render_template("contact.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cur.fetchone()
        cur.close()

        if user and check_password_hash(user["password_hash"], password):
            session["admin"] = user["id"]
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid credentials", "danger")

    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if "admin" not in session:
        return redirect(url_for("login"))

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    cur.execute("SELECT * FROM projects ORDER BY created_at DESC")
    projects = cur.fetchall()

    cur.execute("SELECT * FROM messages ORDER BY created_at DESC")
    messages = cur.fetchall()

    cur.execute("SELECT * FROM blog_posts ORDER BY created_at DESC")
    blogs = cur.fetchall()

    cur.execute("SELECT * FROM certifications ORDER BY created_at DESC")
    certifications = cur.fetchall()

    cur.execute("SELECT * FROM timeline WHERE category='experience' ORDER BY created_at DESC")
    experience = cur.fetchall()

    cur.execute("SELECT * FROM timeline WHERE category='education' ORDER BY created_at DESC")
    education = cur.fetchall()

    cur.close()

    return render_template(
        "dashboard.html",
        projects=projects,
        messages=messages,
        blogs=blogs,
        certifications=certifications,
        experience=experience,
        education=education
    )

@app.route("/blog")
def blog():
    page = request.args.get("page", 1, type=int)
    per_page = 5
    offset = (page - 1) * per_page

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    cur.execute("SELECT COUNT(*) as total FROM blog_posts")
    total_posts = cur.fetchone()["total"]

    cur.execute("""
        SELECT * FROM blog_posts
        ORDER BY created_at DESC
        LIMIT %s OFFSET %s
    """, (per_page, offset))

    posts = cur.fetchall()
    
    for post in posts:
        cur.execute("SELECT image_name FROM blog_images WHERE blog_post_id=%s", (post["id"],))
        post["images"] = cur.fetchall()

    cur.close()

    total_pages = (total_posts + per_page - 1) // per_page

    return render_template(
        "blog.html",
        posts=posts,
        page=page,
        total_pages=total_pages
    )

@app.route("/add-blog", methods=["POST"])
def add_blog():
    if "admin" not in session:
        return redirect(url_for("login"))

    title = request.form["title"]
    content = request.form["content"]

    cur = mysql.connection.cursor()
    
    cur.execute("""
        INSERT INTO blog_posts (title, content)
        VALUES (%s, %s)
    """, (title, content))
    
    blog_post_id = cur.lastrowid

    images = request.files.getlist("images")

    for image in images:
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

            cur.execute("""
                INSERT INTO blog_images (blog_post_id, image_name)
                VALUES (%s, %s)
            """, (blog_post_id, filename))

    mysql.connection.commit()
    cur.close()

    flash("Blog post published!", "success")
    return redirect(url_for("dashboard"))

@app.route("/blog/<int:post_id>")
def blog_detail(post_id):
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM blog_posts WHERE id=%s", (post_id,))
    post = cur.fetchone()
    
    if not post:
        cur.close()
        return "Post not found", 404
        
    cur.execute("SELECT image_name FROM blog_images WHERE blog_post_id=%s", (post_id,))
    post["images"] = cur.fetchall()
    
    cur.close()

    return render_template("blog_detail.html", post=post)

@app.route("/delete-blog/<int:post_id>")
def delete_blog(post_id):
    if "admin" not in session:
        return redirect(url_for("login"))

    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM blog_posts WHERE id=%s", (post_id,))
    mysql.connection.commit()
    cur.close()

    flash("Blog deleted!", "danger")
    return redirect(url_for("dashboard"))

@app.route("/edit-blog/<int:post_id>", methods=["GET", "POST"])
def edit_blog(post_id):
    if "admin" not in session:
        return redirect(url_for("login"))

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]

        cur.execute(
            "UPDATE blog_posts SET title=%s, content=%s WHERE id=%s",
            (title, content, post_id)
        )
        mysql.connection.commit()
        cur.close()

        flash("Blog updated successfully!", "success")
        return redirect(url_for("dashboard"))

    cur.execute("SELECT * FROM blog_posts WHERE id=%s", (post_id,))
    post = cur.fetchone()
    cur.close()

    return render_template("edit_blog.html", post=post)

@app.route("/upload-resume", methods=["POST"])
def upload_resume():
    if "admin" not in session:
        return redirect(url_for("login"))

    file = request.files.get("resume")

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join("static/resume", filename))

        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM resume") 
        cur.execute("INSERT INTO resume (file_name) VALUES (%s)", (filename,))
        mysql.connection.commit()
        cur.close()

        flash("Resume uploaded successfully!", "success")

    return redirect(url_for("dashboard"))

@app.route("/download-resume")
def download_resume():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM resume ORDER BY uploaded_at DESC LIMIT 1")
    resume = cur.fetchone()
    cur.close()

    if not resume:
        return "No resume uploaded yet."

    return redirect(url_for('static', filename='resume/' + resume["file_name"]))

@app.route("/certifications")
def certifications():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    cur.execute("SELECT * FROM certifications ORDER BY created_at DESC")
    certifications = cur.fetchall()
    
    cur.close()

    return render_template("certifications.html", certifications=certifications)

@app.route("/delete-certification/<int:cert_id>")
def delete_certification(cert_id):
    if "admin" not in session:
        return redirect(url_for("login"))

    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM certifications WHERE id=%s", (cert_id,))
    mysql.connection.commit()
    cur.close()

    flash("Certification deleted!", "danger")
    return redirect(url_for("dashboard"))

@app.route("/edit-certification/<int:cert_id>", methods=["GET", "POST"])
def edit_certification(cert_id):
    if "admin" not in session:
        return redirect(url_for("login"))

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    if request.method == "POST":
        name = request.form["name"]
        org = request.form["organization"]
        link = request.form["link"]
        image = request.files.get("image")

        if image and allowed_file(image.filename):

            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            cur.execute("""
                UPDATE certifications 
                SET name=%s, issuing_organization=%s, cert_link=%s, image_name=%s 
                WHERE id=%s
            """, (name, org, link, filename, cert_id))
        else:
            cur.execute("""
                UPDATE certifications 
                SET name=%s, issuing_organization=%s, cert_link=%s 
                WHERE id=%s
            """, (name, org, link, cert_id))

        mysql.connection.commit()
        cur.close()

        flash("Certification updated successfully!", "success")
        return redirect(url_for("dashboard"))

    cur.execute("SELECT * FROM certifications WHERE id=%s", (cert_id,))
    cert = cur.fetchone()
    cur.close()

    return render_template("edit_certification.html", cert=cert)

@app.route("/project/<int:project_id>")
def project_detail(project_id):
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    cur.execute("SELECT * FROM projects WHERE id=%s", (project_id,))
    project = cur.fetchone()
    
    if not project:
        cur.close()
        return "Project not found", 404
        
    cur.execute("SELECT image_name FROM project_images WHERE project_id=%s", (project_id,))
    project["images"] = cur.fetchall()
    
    cur.close()

    return render_template("project_detail.html", project=project)

@app.route("/add-timeline", methods=["POST"])
def add_timeline():
    if "admin" not in session:
        return redirect(url_for("login"))

    category = request.form["category"]
    title = request.form["title"]
    organization = request.form["organization"]
    duration = request.form["duration"]
    description = request.form["description"]

    cur = mysql.connection.cursor()
    cur.execute("""
        INSERT INTO timeline (category, title, organization, duration, description)
        VALUES (%s, %s, %s, %s, %s)
    """, (category, title, organization, duration, description))
    mysql.connection.commit()
    cur.close()

    flash("Timeline entry added successfully!", "success")
    return redirect(url_for("dashboard"))

@app.route("/delete-timeline/<int:entry_id>")
def delete_timeline(entry_id):
    if "admin" not in session:
        return redirect(url_for("login"))

    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM timeline WHERE id=%s", (entry_id,))
    mysql.connection.commit()
    cur.close()

    flash("Timeline entry deleted!", "danger")
    return redirect(url_for("dashboard"))

@app.route("/edit-timeline/<int:entry_id>", methods=["GET", "POST"])
def edit_timeline(entry_id):
    if "admin" not in session:
        return redirect(url_for("login"))

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    if request.method == "POST":
        title = request.form["title"]
        organization = request.form["organization"]
        duration = request.form["duration"]
        description = request.form["description"]

        cur.execute("""
            UPDATE timeline 
            SET title=%s, organization=%s, duration=%s, description=%s 
            WHERE id=%s
        """, (title, organization, duration, description, entry_id))
        
        mysql.connection.commit()
        cur.close()

        flash("Timeline entry updated successfully!", "success")
        return redirect(url_for("dashboard"))

    cur.execute("SELECT * FROM timeline WHERE id=%s", (entry_id,))
    entry = cur.fetchone()
    cur.close()

    return render_template("edit_timeline.html", entry=entry)

@app.route("/journey")
def journey():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    cur.execute("SELECT * FROM timeline WHERE category='experience' ORDER BY created_at DESC")
    experience = cur.fetchall()

    cur.execute("SELECT * FROM timeline WHERE category='education' ORDER BY created_at DESC")
    education = cur.fetchall()
    
    cur.close()

    return render_template("journey.html", experience=experience, education=education)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]

@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)
