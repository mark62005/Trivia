import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10


def fetch_categories():
    categories = Category.query.all()
    return {
        "categories": [cat.format() for cat in categories],
        "total_categories": len(categories)
    }


def get_paginated_questions(request, questions):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    formatted_questions = [question.format() for question in questions]
    paginated_questions = formatted_questions[start:end]
    return paginated_questions


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    db = SQLAlchemy()
    setup_db(app)

    '''
    @TODO: Set up CORS. Allow '*' for origins. Delete the sample route after 
    completing the TODOs
    '''
    CORS(app, resources={r'*': {'origins': '*'}})

    '''
    @TODO: Use the after_request decorator to set Access-Control-Allow
    '''
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers',
                             'Content-Type, Authorization, True')
        response.headers.add('Access-Control-Allow-Headers',
                             'GET, POST, PATCH, DELETE, OPTION')
        return response

    '''
    @TODO:
    Create an endpoint to handle GET requests
    for all available categories.
    '''
    @app.route('/categories', methods=['GET'])
    def get_categories():
        if request.method == 'GET':
            categories = fetch_categories()

            if len(categories['categories']) is None:
                abort(404)

            return jsonify({
                'success': True,
                'categories': categories['categories'],
                'total_categories': categories['total_categories'],
            })

    '''
    @TODO:
    Create an endpoint to handle GET requests for questions,
    including pagination (every 10 questions).
    This endpoint should return a list of questions,
    number of total questions, current category, categories.

    TEST: At this point, when you start the application
    you should see questions and categories generated,
    ten questions per page and pagination at the bottom of the
    screen for three pages.
    Clicking on the page numbers should update the questions.
    '''
    @app.route('/questions', methods=['GET'])
    def get_questions():
        if request.method == 'GET':
            questions = Question.query.order_by(Question.id).all()
            categories = fetch_categories()

            current_questions = get_paginated_questions(request, questions)

            if len(current_questions) == 0 or\
                    len(categories['categories']) == 0:
                abort(404)

            return jsonify({
                'success': True,
                'questions': current_questions,
                'total_questions': len(questions),
                'categories': categories['categories'],
                'current_category': None
            })

    '''
    @TODO:
    Create an endpoint to DELETE question using a question ID.

    TEST: When you click the trash icon next to a question, the question will
    be removed.
    This removal will persist in the database and when you refresh the page.
    '''
    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):
        if request.method == 'DELETE':
            error = False
            question = Question.query.filter(
                Question.id == question_id).one_or_none()

            if question is None:
                abort(404)

            try:
                question.delete()
            except Exception as e:
                error = True
                print(e)
                db.session.rollback()
            finally:
                db.session.close()

            if error:
                abort(422)
            else:
                return jsonify({
                    'success': True,
                    'deleted': question_id
                })

    '''
    @TODO:
    Create an endpoint to POST a new question,
    which will require the question and answer text,
    category, and difficulty score.

    TEST: When you submit a question on the "Add" tab,
    the form will clear and the question will appear at the end of
    the last page
    of the questions list in the "List" tab.
    '''
    @app.route('/questions', methods=['POST'])
    def create_question():
        if request.method == 'POST':
            error = False
            body = request.get_json()

            new_question = body.get('question')
            new_answer = body.get('answer')
            new_difficulty = body.get('difficulty', 1)
            new_question_category = body.get('category', 1)

            if new_question is None or new_answer is None:
                abort(422)

            question = Question(
                question=new_question,
                answer=new_answer,
                difficulty=new_difficulty,
                category=new_question_category
            )

            try:
                question.insert()
            except Exception as e:
                error = True
                print(e)
                db.session.rollback()
            finally:
                db.session.close()

            if error:
                abort(422)
            else:
                return jsonify({
                    'success': True,
                    'created': question.id,
                    'total_questions': Question.query.count()
                })

    '''
    @TODO:
    Create a POST endpoint to get questions based on a search term.
    It should return any questions for whom the search term
    is a substring of the question.

    TEST: Search by any phrase. The questions list will update to include
    only question that include that string within their question.
    Try using the word "title" to start.
    '''
    @app.route('/questions/search', methods=['POST'])
    def search_questions():
        if request.method == 'POST':
            body = request.get_json()
            search = body.get('search_term', None).strip()

            try:
                matched_questions = \
                    Question.query.filter(
                        Question.question.ilike(f'%{search}%')
                    ).order_by(Question.category).all()

                return jsonify({
                    'success': True,
                    'questions':
                    get_paginated_questions(request, matched_questions),
                    'total_questions': len(matched_questions),
                    'current_category': None
                })
            except Exception as e:
                print(e)
                abort(422)

    '''
    @TODO:
    Create a GET endpoint to get questions based on category.

    TEST: In the "List" tab / main screen, clicking on one of the
    categories in the left column will cause only questions of that
    category to be shown.
    '''
    @app.route('/categories/<int:category_id>/questions', methods=['GET'])
    def get_questions_by_category(category_id):
        if request.method == 'GET':
            category = Category.query.filter(
                Category.id == category_id).one_or_none()

            if category is None:
                abort(404)

            try:
                matched_questions = \
                    category.questions.order_by(Question.question).all()

                current_questions = get_paginated_questions(
                    request, matched_questions)

                return jsonify({
                    'success': True,
                    'questions': current_questions,
                    'total_questions': len(matched_questions),
                    'current_category': category.format()
                })
            except Exception as e:
                print(e)
                abort(400)

    '''
    @TODO: 
    Create a POST endpoint to get questions to play the quiz. 
    This endpoint should take category and previous question parameters 
    and return a random questions within the given category, 
    if provided, and that is not one of the previous questions.

    TEST: In the "Play" tab, after a user selects "All" or a category,
    one question at a time is displayed, the user is allowed to answer
    and shown whether they were correct or not.
    '''

    '''
    @TODO:
    Create error handlers for all expected errors
    including 404 and 422.
    '''
    @app.errorhandler(404)
    def resource_not_found(error):
        return jsonify({
            'success': False,
            'error': 404,
            'message': 'resource not found'
        }), 404

    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({
            'success': False,
            'error': 422,
            'message': 'unprocessable'
        }), 422

    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
            'success': False,
            'error': 405,
            'message': 'method not allowed'
        }), 405

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'success': False,
            'error': 400,
            'message': 'bad request'
        }), 400

    return app
