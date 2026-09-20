document.addEventListener("DOMContentLoaded", function () {

    console.log("Shipment Intelligence Dashboard loaded");


    /* =====================================================
       MONTHLY SHIPMENT CHART
    ===================================================== */

    const monthlyCanvas =
        document.getElementById("monthlyChart");

    if (monthlyCanvas) {

        new Chart(monthlyCanvas, {

            type: "line",

            data: {

                labels:
                    window.monthlyLabels || [],

                datasets: [

                    {

                        label: "Shipments",

                        data:
                            window.monthlyValues || [],

                        borderColor: "#2563eb",

                        backgroundColor:
                            "rgba(37,99,235,0.12)",

                        borderWidth: 3,

                        fill: true,

                        tension: 0.4,

                        pointRadius: 3,

                        pointHoverRadius: 6

                    }

                ]

            },

            options: {

                responsive: true,

                maintainAspectRatio: false,

                plugins: {

                    legend: {
                        display: false
                    }

                },

                scales: {

                    y: {

                        beginAtZero: true,

                        grid: {
                            color: "#eef2f7"
                        }

                    },

                    x: {

                        grid: {
                            display: false
                        }

                    }

                }

            }

        });

    }


    /* =====================================================
       CARRIER CHART
    ===================================================== */

    const carrierCanvas =
        document.getElementById("carrierChart");

    if (carrierCanvas) {

        new Chart(carrierCanvas, {

            type: "bar",

            data: {

                labels:
                    window.carrierLabels || [],

                datasets: [

                    {

                        label: "Delay Rate",

                        data:
                            window.carrierValues || [],

                        backgroundColor: "#ef4444",

                        borderRadius: 6,

                        borderWidth: 0

                    }

                ]

            },

            options: {

                responsive: true,

                maintainAspectRatio: false,

                plugins: {

                    legend: {
                        display: false
                    }

                },

                scales: {

                    y: {

                        beginAtZero: true,

                        max: 100,

                        ticks: {

                            callback: function(value) {

                                return value + "%";

                            }

                        }

                    },

                    x: {

                        grid: {
                            display: false
                        }

                    }

                }

            }

        });

    }


    /* =====================================================
       REGION CHART
    ===================================================== */

    const regionCanvas =
        document.getElementById("regionChart");

    if (regionCanvas) {

        new Chart(regionCanvas, {

            type: "bar",

            data: {

                labels:
                    window.regionLabels || [],

                datasets: [

                    {

                        label: "Delay Rate",

                        data:
                            window.regionValues || [],

                        backgroundColor: "#8b5cf6",

                        borderRadius: 6,

                        borderWidth: 0

                    }

                ]

            },

            options: {

                indexAxis: "y",

                responsive: true,

                maintainAspectRatio: false,

                plugins: {

                    legend: {
                        display: false
                    }

                },

                scales: {

                    x: {

                        beginAtZero: true,

                        max: 100,

                        ticks: {

                            callback: function(value) {

                                return value + "%";

                            }

                        }

                    }

                }

            }

        });

    }


    /* =====================================================
       SHIPPING MODE CHART
    ===================================================== */

    const modeCanvas =
        document.getElementById("modeChart");

    if (modeCanvas) {

        new Chart(modeCanvas, {

            type: "doughnut",

            data: {

                labels:
                    window.modeLabels || [],

                datasets: [

                    {

                        data:
                            window.modeValues || [],

                        backgroundColor: [

                            "#2563eb",

                            "#16a34a",

                            "#f59e0b",

                            "#8b5cf6",

                            "#ef4444"

                        ],

                        borderWidth: 3,

                        borderColor: "#ffffff"

                    }

                ]

            },

            options: {

                responsive: true,

                maintainAspectRatio: false,

                cutout: "65%",

                plugins: {

                    legend: {

                        position: "bottom",

                        labels: {

                            padding: 15,

                            usePointStyle: true

                        }

                    }

                }

            }

        });

    }


    /* =====================================================
       KPI API
    ===================================================== */

    async function updateKPIs() {

        try {

            const response =
                await fetch("/api/kpis");

            if (!response.ok) {

                throw new Error(
                    "KPI request failed"
                );

            }

            const data =
                await response.json();


            const total =
                document.getElementById(
                    "totalShipments"
                );

            if (total) {

                total.textContent =
                    data.total_shipments;

            }


            const delayed =
                document.getElementById(
                    "delayedShipments"
                );

            if (delayed) {

                delayed.textContent =
                    data.delayed_shipments;

            }


            const rate =
                document.getElementById(
                    "delayRate"
                );

            if (rate) {

                rate.textContent =
                    data.delay_rate + "%";

            }


            const delivery =
                document.getElementById(
                    "avgDelivery"
                );

            if (delivery) {

                delivery.textContent =
                    data.avg_delivery;

            }


            const anomalies =
                document.getElementById(
                    "anomalyCount"
                );

            if (anomalies) {

                anomalies.textContent =
                    data.anomalies;

            }

        }

        catch (error) {

            console.error(
                "KPI error:",
                error
            );

        }

    }


    updateKPIs();


    /* =====================================================
       MOBILE SIDEBAR
    ===================================================== */

    const menuButton =
        document.getElementById(
            "menuButton"
        );

    const sidebar =
        document.getElementById(
            "sidebar"
        );


    if (menuButton && sidebar) {

        menuButton.addEventListener(
            "click",
            function () {

                sidebar.classList.toggle(
                    "active"
                );

            }
        );

    }


    console.log(
        "Dashboard initialized successfully"
    );

});