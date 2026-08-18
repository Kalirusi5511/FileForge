import os

from flask import Blueprint
from flask import jsonify
from flask import render_template
from flask import request

from flask_mail import Mail
from flask_mail import Message

feedback_bp = Blueprint(
    "feedback",
    __name__,
    template_folder="templates"
)

mail = Mail()


def init_mail(app):

    app.config["MAIL_SERVER"] = os.environ.get("MAIL_SERVER")
    app.config["MAIL_PORT"] = int(
        os.environ.get("MAIL_PORT", 587)
    )

    app.config["MAIL_USE_TLS"] = True
    app.config["MAIL_USE_SSL"] = False

    app.config["MAIL_USERNAME"] = os.environ.get(
        "EMAIL_ADDRESS"
    )

    app.config["MAIL_PASSWORD"] = os.environ.get(
        "EMAIL_PASSWORD"
    )

    mail.init_app(app)


@feedback_bp.route("/feedback")
def feedback():

    return render_template("feedback.html")


@feedback_bp.route(
    "/send-feedback",
    methods=["POST"]
)
def send_feedback():

    try:

        name = request.form.get("name")
        email = request.form.get("email")
        text = request.form.get("message")

        msg = Message(
            subject=f"Neue Nachricht von {name}",
            sender=os.environ.get(
                "EMAIL_ADDRESS"
            ),
            recipients=[
                os.environ.get(
                    "EMAIL_ADDRESS"
                )
            ]
        )

        msg.body = f"""
Name: {name}

E-Mail: {email}

Nachricht:

{text}
"""

        mail.send(msg)

        return jsonify(
            {
                "success": True
            }
        )

    except Exception as error:

        return jsonify(
            {
                "success": False,
                "error": str(error)
            }
        )
