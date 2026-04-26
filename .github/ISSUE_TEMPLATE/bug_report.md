name: Bug Report
description: Report a bug or issue
title: "[BUG] "
labels: ["bug"]

body:
  - type: markdown
    attributes:
      value: |
        Thanks for reporting! Please provide details below.

  - type: textarea
    id: description
    attributes:
      label: Describe the Bug
      description: Clear description of what went wrong
      placeholder: "What happened?"
    validations:
      required: true

  - type: textarea
    id: reproduction
    attributes:
      label: Steps to Reproduce
      description: How can we reproduce this bug?
      placeholder: |
        1. 
        2. 
        3.
    validations:
      required: true

  - type: textarea
    id: expected
    attributes:
      label: Expected Behavior
      description: What should happen?
    validations:
      required: true

  - type: textarea
    id: logs
    attributes:
      label: Error Logs or Stack Trace
      description: Paste any relevant error messages
      render: shell

  - type: textarea
    id: environment
    attributes:
      label: Environment
      description: Include Python version, OS, GPU info
      placeholder: |
        - OS: 
        - Python: 
        - PyTorch: 
        - GPU: 
    validations:
      required: true

  - type: checkboxes
    id: checklist
    attributes:
      label: Checklist
      options:
        - label: I searched existing issues
          required: true
        - label: I can reproduce the issue
          required: true
