{% extends "layout/base.html" %}
{% block title %}Dashboard{% endblock %}

{% block content %}
<h2>Welcome, {{ current_user.username }}</h2>

<div class="dashboard">
    <div class="card">
        <h3>Members</h3>
        <p>View and search member records</p>
        <a href="/admin/members-test">Open</a>
    </div>

    <div class="card">
        <h3>Reports</h3>
        <p>Summary & statistics</p>
        <span class="muted">Coming soon</span>
    </div>

    <div class="card">
        <h3>Administration</h3>
        <p>User & system settings</p>
        <span class="muted">Restricted</span>
    </div>
</div>
{% endblock %}
