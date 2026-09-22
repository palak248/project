(function () {
    "use strict";

    function readData(elementId) {
        var element = document.getElementById(elementId);
        if (!element) {
            return [];
        }

        try {
            return JSON.parse(element.textContent) || [];
        } catch (error) {
            return [];
        }
    }

    function showEmpty(canvasId, messageId) {
        var canvas = document.getElementById(canvasId);
        var message = document.getElementById(messageId);
        if (canvas) {
            canvas.hidden = true;
        }
        if (message) {
            message.hidden = false;
        }
    }

    function subjectLabel(subject) {
        return subject.subject_code
            ? subject.subject_name + " (" + subject.subject_code + ")"
            : subject.subject_name;
    }

    function renderSubjectCharts(subjects) {
        if (!subjects.length) {
            showEmpty("subject-marks-chart", "subject-marks-empty");
            showEmpty("marks-distribution-chart", "marks-distribution-empty");
            return;
        }

        var labels = subjects.map(subjectLabel);
        var obtainedMarks = subjects.map(function (subject) {
            return Number(subject.obtained_marks);
        });
        var maximumMarks = subjects.map(function (subject) {
            return Number(subject.maximum_marks);
        });

        new Chart(document.getElementById("subject-marks-chart"), {
            type: "bar",
            data: {
                labels: labels,
                datasets: [
                    {
                        label: "Obtained marks",
                        data: obtainedMarks,
                        backgroundColor: "#176b5b"
                    },
                    {
                        label: "Maximum marks",
                        data: maximumMarks,
                        backgroundColor: "#b7c9c5"
                    }
                ]
            },
            options: {
                maintainAspectRatio: false,
                responsive: true,
                scales: { y: { beginAtZero: true } }
            }
        });

        new Chart(document.getElementById("marks-distribution-chart"), {
            type: "doughnut",
            data: {
                labels: labels,
                datasets: [{
                    label: "Obtained marks",
                    data: obtainedMarks,
                    backgroundColor: ["#176b5b", "#2b8a78", "#64b3a0", "#b7c9c5", "#d99b00", "#a61b1b"]
                }]
            },
            options: {
                maintainAspectRatio: false,
                responsive: true
            }
        });
    }

    function renderTimeChart(results) {
        var datedExaminations = results.filter(function (result) {
            return result.assessment_type === "examination" && result.assessment_date;
        }).sort(function (left, right) {
            return left.assessment_date.localeCompare(right.assessment_date);
        });

        if (datedExaminations.length < 2) {
            showEmpty("performance-time-chart", "performance-time-empty");
            return;
        }

        new Chart(document.getElementById("performance-time-chart"), {
            type: "line",
            data: {
                labels: datedExaminations.map(function (result) {
                    return result.assessment_date + " - " + result.title;
                }),
                datasets: [{
                    label: "Obtained marks",
                    data: datedExaminations.map(function (result) {
                        return Number(result.obtained_marks);
                    }),
                    borderColor: "#176b5b",
                    backgroundColor: "#176b5b",
                    tension: 0.2
                }]
            },
            options: {
                maintainAspectRatio: false,
                responsive: true,
                scales: { y: { beginAtZero: true } }
            }
        });
    }

    document.addEventListener("DOMContentLoaded", function () {
        if (typeof Chart === "undefined") {
            showEmpty("subject-marks-chart", "subject-marks-empty");
            showEmpty("marks-distribution-chart", "marks-distribution-empty");
            showEmpty("performance-time-chart", "performance-time-empty");
            return;
        }

        renderSubjectCharts(readData("student-subject-data"));
        renderTimeChart(readData("student-result-data"));
    });
}());