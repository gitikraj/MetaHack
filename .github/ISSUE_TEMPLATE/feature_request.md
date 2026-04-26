name: Feature Request
description: Suggest a new feature or improvement
title: "[FEATURE] "
labels: ["enhancement"]

body:
  - type: markdown
    attributes:
      value: |
        Thanks for the suggestion! Describe your idea below.

  - type: textarea
    id: description
    attributes:
      label: Feature Description
      description: Clear description of the feature
      placeholder: "What feature would you like to add?"
    validations:
      required: true

  - type: textarea
    id: motivation
    attributes:
      label: Motivation
      description: Why would this be useful?
      placeholder: "How would this improve the project?"
    validations:
      required: true

  - type: textarea
    id: solution
    attributes:
      label: Proposed Solution
      description: How would you implement this?
      placeholder: "Any ideas on how to implement this?"

  - type: textarea
    id: alternatives
    attributes:
      label: Alternatives
      description: Any alternative approaches?

  - type: checkboxes
    id: checklist
    attributes:
      label: Checklist
      options:
        - label: This doesn't duplicate existing issues
          required: true
        - label: I've searched for similar features
          required: true
