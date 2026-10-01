# Constructed rule-verification suite.
# S1-S14: original suite from the manuscript (labels as in the manuscript, except
# S2 which is re-labelled "distress" because hopelessness/worthlessness are
# depressive symptoms, not suicidal intent).
# A1-A12: adversarial cases added in revision: a negation / third-party /
# idiom cue co-occurs with an affirmative first-person crisis statement.
SUITE = [
 ("S1","I want to kill myself, I cannot handle this.",1),
 ("S2","I feel so hopeless and worthless every day.",0),
 ("S3","I am going to end my life tonight.",1),
 ("S4","There is no reason to live for me.",1),
 ("S5","Thinking about suicide constantly.",1),
 ("S6","I do not want to kill myself, just stressed.",0),
 ("S7","I would never commit suicide, love family.",0),
 ("S8","I am not hopeless, things are getting better.",0),
 ("S9","My friend told me she wanted to die.",0),
 ("S10","Watched a movie about suicide yesterday.",0),
 ("S11","We were just trying to kill time before flight.",0),
 ("S12","I almost died laughing at that joke.",0),
 ("S13","She was killing it on stage tonight.",0),
 ("S14","No intention of dying, just exhausted.",0),
 ("A1","I'm not okay, I want to kill myself.",1),
 ("A2","No one cares, I want to die.",1),
 ("A3","I don't know anymore, I want to end my life.",1),
 ("A4","I can't stop thinking about suicide.",1),
 ("A5","My friend says it gets better but I want to die.",1),
 ("A6","Work was killing it today but tonight I want to end my life.",1),
 ("A7","I'm a terrible person and I want to die.",1),
 ("A8","They would all be better off without me.",1),
 ("A9","I never thought I'd say this, I want to kill myself.",1),
 ("A10","I don't want to live anymore.",1),
 ("A11","I used to be suicidal but not anymore, I don't want to die.",0),
 ("A12","My sister has been suicidal and I am scared for her.",0),
]
