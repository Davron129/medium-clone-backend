import pytest
from django.core.exceptions import ValidationError
from django.db import models
from rest_framework import serializers
from users.serializers import UserUpdateSerializer
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
def test_custom_user_meta_class():

    birth_year_field = User._meta.get_field('birth_year')
    assert isinstance(birth_year_field, models.IntegerField)
    assert birth_year_field.validators[0].limit_value == settings.BIRTH_YEAR_MIN
    assert birth_year_field.validators[1].limit_value == settings.BIRTH_YEAR_MAX

    user = User(birth_year=settings.BIRTH_YEAR_MIN - 1)
    with pytest.raises(ValidationError):
        user.clean()

    user = User(birth_year=settings.BIRTH_YEAR_MAX + 1)
    with pytest.raises(ValidationError):
        user.clean()

    user = User(birth_year=(settings.BIRTH_YEAR_MIN + settings.BIRTH_YEAR_MAX) // 2)
    user.clean()

    indexes = User._meta.indexes
    assert any(index.name == 'customuser_first_name_hash_idx' for index in indexes)
    assert any(index.name == 'customuser_last_name_hash_idx' for index in indexes)
    assert any(index.name == 'customuser_middle_name_hash_idx' for index in indexes)
    assert any(index.name == 'customuser_username_idx' for index in indexes)


    constraints = User._meta.constraints
    assert any(constraint.name == 'check_birth_year_range' for constraint in constraints)



VALID_BIRTH_YEAR = (settings.BIRTH_YEAR_MIN + settings.BIRTH_YEAR_MAX) // 2
INVALID_BIRTH_YEAR_LOW = settings.BIRTH_YEAR_MIN - 1
INVALID_BIRTH_YEAR_HIGH = settings.BIRTH_YEAR_MAX + 1

@pytest.mark.parametrize("birth_year, is_valid", [
    (VALID_BIRTH_YEAR, True),
    (INVALID_BIRTH_YEAR_LOW, False),
    (INVALID_BIRTH_YEAR_HIGH, False)
])
def test_validate_birth_year(birth_year, is_valid):
    serializer = UserUpdateSerializer(data={'birth_year': birth_year})
    if is_valid:
        assert serializer.is_valid()
    else:
        with pytest.raises(serializers.ValidationError):
            serializer.is_valid(raise_exception=True)


def test_validate_method():

    valid_data = {'birth_year': VALID_BIRTH_YEAR}
    serializer = UserUpdateSerializer(data=valid_data)
    assert serializer.is_valid()


    invalid_data_low = {'birth_year': INVALID_BIRTH_YEAR_LOW}
    serializer = UserUpdateSerializer(data=invalid_data_low)
    with pytest.raises(serializers.ValidationError) as excinfo:
        serializer.is_valid(raise_exception=True)
    assert 'birth_year' in excinfo.value.detail


    invalid_data_high = {'birth_year': INVALID_BIRTH_YEAR_HIGH}
    serializer = UserUpdateSerializer(data=invalid_data_high)
    with pytest.raises(serializers.ValidationError) as excinfo:
        serializer.is_valid(raise_exception=True)
    assert 'birth_year' in excinfo.value.detail
