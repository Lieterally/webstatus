from app import app, run_monitor_cycle
with app.app_context():
    run_monitor_cycle()