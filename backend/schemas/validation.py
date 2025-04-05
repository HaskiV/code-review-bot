from marshmallow import Schema, fields, validate

class CodeReviewSchema(Schema):
    """Схема для валидации запроса на анализ кода"""
    code = fields.String(required=True, validate=validate.Length(min=1))
    language = fields.String(required=True, validate=validate.OneOf(["python", "javascript", "java", "cpp"]))
    model_id = fields.String(required=False)

class ModelSchema(Schema):
    """Схема для валидации запроса на создание модели"""
    id = fields.String(required=True)
    name = fields.String(required=True)
    type = fields.String(required=True, validate=validate.OneOf(["openai", "anthropic", "huggingface", "mock"]))
    config = fields.Dict(required=False)
    is_default = fields.Boolean(required=False, default=False)

class ModelUpdateSchema(Schema):
    """Схема для валидации запроса на обновление модели"""
    name = fields.String(required=False)
    type = fields.String(required=False, validate=validate.OneOf(["openai", "anthropic", "huggingface", "mock"]))
    config = fields.Dict(required=False)
    is_default = fields.Boolean(required=False)