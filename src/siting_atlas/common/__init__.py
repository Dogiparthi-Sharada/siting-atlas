"""Cross-cutting concerns: paths, context, logging, tracing, IO wrappers.

Import order matters only in that `logging_setup.configure()` should be called
once by the entry point before other modules emit records.
"""
