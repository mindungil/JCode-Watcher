from app.models.process import Process
from app.student_parser import StudentParser


def process(hostname: str) -> Process:
    return Process(
        pid=1,
        binary_path="/usr/bin/python3",
        cwd="/home/coder/project",
        args=[],
        error_flags="0b0",
        exit_code=0,
        hostname=hostname,
    )


def test_stable_assignment_hostname_contains_assignment_identity():
    parsed = StudentParser().parse_from_process(process("jcode-os-1-20260001-42"))

    assert parsed is not None
    assert parsed.class_div == "os-1"
    assert parsed.student_id == "20260001"
    assert parsed.assignment_id == 42


def test_replica_suffix_is_not_misclassified_as_assignment_identity():
    parsed = StudentParser().parse_from_process(
        process("jcode-os-1-20260001-6d4b7c8f9b-r2d2x")
    )

    assert parsed is not None
    assert parsed.assignment_id is None
