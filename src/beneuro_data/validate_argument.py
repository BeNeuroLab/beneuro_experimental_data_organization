import inspect


def validate_argument(arg_name, valid_values):
    def decorator(func):
        from functools import wraps

        @wraps(func)
        def wrapper(*args, **kwargs):
            # Fetch the value of the argument by name
            arg_value = kwargs.get(arg_name)

            # If the value is not in kwargs, try positional args
            if arg_value is None and len(args) > 0:
                # Using inspect to get a clearer picture of the parameters
                sig = inspect.signature(func)
                bound_args = sig.bind(*args, **kwargs)
                arg_value = bound_args.arguments.get(arg_name)

            # Check if the value is in the valid set
            if arg_value not in valid_values:
                raise ValueError(
                    f"Invalid value for {arg_name}. Valid values are: {', '.join(map(str, valid_values))}. Got {arg_value}"
                )

            return func(*args, **kwargs)

        return wrapper

    return decorator
