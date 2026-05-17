document.addEventListener('DOMContentLoaded', () => {
    // 1. Navigation Highlighting
    const currentPath = window.location.pathname;
    const navLinks = {
        '/': 'nav-home',
        '/live': 'nav-live',
        '/dashboard': 'nav-dashboard',
        '/how-it-works': 'nav-how',
        '/impact': 'nav-impact',
        '/team': 'nav-team'
    };

    const activeId = navLinks[currentPath];
    if (activeId) {
        const activeLink = document.getElementById(activeId);
        if (activeLink) activeLink.classList.add('active');
    }

    // 2. Count-up Animation for Dashboard
    const stats = document.querySelectorAll('.stat-number');
    const animateValue = (obj, start, end, duration) => {
        let startTimestamp = null;
        const step = (timestamp) => {
            if (!startTimestamp) startTimestamp = timestamp;
            const progress = Math.min((timestamp - startTimestamp) / duration, 1);
            const current = Math.floor(progress * (end - start) + start);
            obj.innerHTML = current.toLocaleString();
            if (progress < 1) {
                window.requestAnimationFrame(step);
            }
        };
        window.requestAnimationFrame(step);
    };

    if (stats.length > 0) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const target = parseInt(entry.target.getAttribute('data-target'));
                    animateValue(entry.target, 0, target, 2000);
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.5 });
        stats.forEach(stat => observer.observe(stat));
    }

    // 3. Advanced How It Works - Teardown Logic
    const partData = {
        'esp32': {
            title: "ESP32-CAM",
            description: "A low-cost, small-form-factor module that handles both high-resolution camera tasks and Wi-Fi connectivity. It streams the live video feed directly to the web application.",
            connection: "Connected to the vision system and powered by the 5V regulator. Communicates via Wi-Fi.",
            orbit: "0deg 70deg 1.2m",
            target: "0.4m 0.4m 0m",
            modelFile: "esp32-cam_dummy.glb"
        },
        'arduino': {
            title: "Arduino Uno / Nano",
            description: "The primary microcontroller responsible for low-level hardware control. It manages motor movements, servo articulations, and sensor feedback.",
            connection: "Acts as the brain for physical actions, receiving high-level commands and executing precise motor control.",
            orbit: "45deg 75deg 1.5m",
            target: "0m 0.3m 0m",
            modelFile: "arduino_uno.glb"
        },
        'camera': {
            title: "OV2640 Camera Module",
            description: "A compact CMOS image sensor that captures the real-time visual data required for the AI-driven weed detection system.",
            connection: "Integrated into the ESP32-CAM module, positioned at the front of the rover for an optimal field of view.",
            orbit: "0deg 80deg 1.2m",
            target: "0.5m 0.35m 0m",
            modelFile: "esp32-cam_dummy.glb"
        },
        'l298n': {
            title: "L298N Motor Driver",
            description: "A high-power dual H-bridge driver used to control the speed and direction of the four DC gear motors.",
            connection: "Interfaced between the Arduino and the drive motors. Connected directly to the main battery pack.",
            orbit: "90deg 80deg 1.5m",
            target: "0.1m 0.2m 0.2m",
            modelFile: "l298n_motor_driver.glb"
        },
        'chassis': {
            title: "4WD Car Chassis",
            description: "An acrylic and structured base that provides the physical foundation for all electronic and mechanical components.",
            connection: "Mounting point for motors, electronics boards, and the protective cardboard outer shell.",
            orbit: "45deg 75deg 2m",
            target: "0m 0.15m 0m",
            modelFile: "4wd_smart_buggy_chassis.glb"
        },
        'motors': {
            title: "DC Gear Motors",
            description: "Four high-torque geared motors that provide reliable movement across agricultural terrain.",
            connection: "Attached to the chassis corners and driven by the L298N motor controller.",
            orbit: "120deg 85deg 1.8m",
            target: "0.3m 0.1m 0.3m",
            modelFile: "4wd_smart_buggy_chassis.glb"
        },
        'arm-servos': {
            title: "Servo Actuators",
            description: "High-torque MG996R servos handle the heavy lifting of the arm links, while SG90/MG90S servos manage the precise gripper movements.",
            connection: "Powered by the 5V buck converter and controlled via PWM signals from the Arduino.",
            orbit: "-30deg 60deg 1.5m",
            target: "0.2m 0.5m 0.1m",
            modelFile: "micro_servo_motor.glb"
        },
        'claw': {
            title: "Gripper System",
            description: "A custom 2 or 3-finger claw designed specifically for gripping and plucking weeds without damaging surrounding crops.",
            connection: "The end-effector of the robotic arm, actuated by a dedicated servo for open/close functionality.",
            orbit: "-40deg 50deg 1.2m",
            target: "0.6m 0.4m 0m",
            modelFile: "mechanical_arm.glb"
        },
        'basket': {
            title: "Collection Basket",
            description: "A lightweight container used to store removed plant matter for later composting and nutrient recycling.",
            connection: "Securely mounted to the rear of the chassis, easily accessible for manual emptying.",
            orbit: "180deg 70deg 2m",
            target: "-0.4m 0.3m 0m"
        },
        'power': {
            title: "Li-Ion Battery Pack",
            description: "A high-capacity (7.4V or 12V) rechargeable lithium battery providing the necessary amperage for heavy-duty motor operations.",
            connection: "The central power source, feeding the motor driver and the 5V voltage regulator.",
            orbit: "-150deg 70deg 1.8m",
            target: "-0.2m 0.2m 0m"
        },
        'regulator': {
            title: "5V Buck Converter",
            description: "Step-down voltage regulator that converts high battery voltage into a stable 5V supply for the Arduino and ESP32.",
            connection: "Connected between the main battery and the logic components to prevent overvoltage damage.",
            orbit: "-120deg 80deg 1.5m",
            target: "0m 0.3m -0.1m"
        },
        'indicators': {
            title: "LEDs & Buzzer",
            description: "Visual (Green/Red LEDs) and audible (Buzzer) indicators providing real-time feedback on system status and weed detection.",
            connection: "Controlled by digital pins on the Arduino for immediate operator feedback.",
            orbit: "20deg 70deg 1.2m",
            target: "0.3m 0.4m 0.1m"
        }
    };

    const modelObj = document.getElementById('teardown-model');
    const detailPanel = document.getElementById('detail-panel');
    const partTitle = document.getElementById('part-title');
    const partDesc = document.getElementById('part-description');
    const partConn = document.getElementById('part-connection');
    const partModelContainer = document.getElementById('part-model-container');
    const partModelViewer = document.getElementById('part-model-viewer');
    const btnDisassemble = document.getElementById('btn-disassemble');
    const btnReassemble = document.getElementById('btn-reassemble');
    const btnResetView = document.getElementById('btn-reset-view');
    const activeControls = document.getElementById('teardown-active-controls');
    const partItems = document.querySelectorAll('.part-item');
    const hotspots = document.querySelectorAll('.hotspot');
    const workflowSteps = document.querySelectorAll('.step-node');

    let isExploded = false;

    const selectPart = (partKey) => {
        if (!isExploded) return;
        
        const data = partData[partKey];
        if (!data) return;

        partTitle.innerText = data.title;
        partDesc.innerText = data.description;
        partConn.innerText = data.connection;
        detailPanel.classList.add('active');

        // Update secondary model viewer
        if (data.modelFile) {
            partModelContainer.style.display = 'block';
            partModelViewer.src = `/static/models/${data.modelFile}`;
        } else {
            partModelContainer.style.display = 'none';
        }

        partItems.forEach(item => {
            item.classList.toggle('active', item.getAttribute('data-part') === partKey);
        });

        if (modelObj) {
            modelObj.cameraOrbit = data.orbit;
            modelObj.cameraTarget = data.target;

            // Simple pulse highlight for selection
            if (modelObj.model && modelObj.model.materials) {
                modelObj.model.materials.forEach(material => {
                    material.pbrMetallicRoughness.setBaseColorFactor([1, 1, 1, 1]);
                });
                const mat = modelObj.model.materials[0];
                if (mat) mat.pbrMetallicRoughness.setBaseColorFactor([0.13, 0.77, 0.37, 1]);
            }
        }
    };

    if (modelObj) {
        hotspots.forEach(h => h.style.display = 'none');

        hotspots.forEach(hotspot => {
            hotspot.addEventListener('click', () => selectPart(hotspot.getAttribute('data-part')));
        });

        partItems.forEach(item => {
            item.addEventListener('click', () => {
                if (!isExploded) btnDisassemble?.click();
                setTimeout(() => selectPart(item.getAttribute('data-part')), 100);
            });
        });

        btnDisassemble?.addEventListener('click', () => {
            isExploded = true;
            modelObj.classList.add('exploded');
            btnDisassemble.style.display = 'none';
            activeControls.style.display = 'flex';
            hotspots.forEach(h => h.style.display = 'block');
            modelObj.cameraOrbit = "0deg 75deg 3m";
            modelObj.cameraTarget = "0m 0.5m 0m";
        });

        btnReassemble?.addEventListener('click', () => {
            isExploded = false;
            modelObj.classList.remove('exploded');
            activeControls.style.display = 'none';
            btnDisassemble.style.display = 'block';
            detailPanel.classList.remove('active');
            partModelContainer.style.display = 'none';
            partItems.forEach(i => i.classList.remove('active'));
            hotspots.forEach(h => h.style.display = 'none');
            modelObj.cameraOrbit = "auto auto auto";
            modelObj.cameraTarget = "auto auto auto";
            if (modelObj.model && modelObj.model.materials) {
                modelObj.model.materials.forEach(m => m.pbrMetallicRoughness.setBaseColorFactor([1,1,1,1]));
            }
        });

        btnResetView?.addEventListener('click', () => {
            detailPanel.classList.remove('active');
            partModelContainer.style.display = 'none';
            partItems.forEach(i => i.classList.remove('active'));
            modelObj.cameraOrbit = "0deg 75deg 3m";
            modelObj.cameraTarget = "0m 0.5m 0m";
            if (modelObj.model && modelObj.model.materials) {
                modelObj.model.materials.forEach(m => m.pbrMetallicRoughness.setBaseColorFactor([1,1,1,1]));
            }
        });

        workflowSteps.forEach(step => {
            step.addEventListener('click', () => {
                if (!isExploded) btnDisassemble?.click();
                workflowSteps.forEach(s => s.classList.remove('active'));
                step.classList.add('active');
                const stepKey = step.getAttribute('data-step');
                const stepMap = {
                    'capture': 'camera', 'detect': 'esp32', 'target': 'arduino', 'remove': 'arm-servos', 'collect': 'basket'
                };
                setTimeout(() => selectPart(stepMap[stepKey]), 100);
            });
        });
    }

    // 4. Smooth Transitions
    const cards = document.querySelectorAll('.card, .part-item, .step-node');
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        card.style.transition = `all 0.6s cubic-bezier(0.22, 1, 0.36, 1) ${index * 0.05}s`;
        setTimeout(() => {
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, 100);
    });
});
