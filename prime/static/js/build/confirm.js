var Skills = React.createClass({displayName: "Skills",
    render: function() {
        var skills = this.props.data.map(function(skill) {
            return (
                React.createElement("div", {className: "skill"}, 
                    skill, 
                    React.createElement("span", {"data-delete": skill, className: "delete"}, "X")
                )
                )
        });
        return (
            React.createElement("div", {className: "skills"}, 
                skills
            )
            )
    }
});

var NewJob = React.createClass({displayName: "NewJob",
    render: function() {
    return (
      React.createElement("div", {className: "search-box row"}, 
        React.createElement("h1", null, "Add School"), 
        React.createElement("h4", null, this.props.name), 
        React.createElement("form", {action: "/jobs/create", method: "POST"}, 
            React.createElement("input", {type: "hidden", name: "company_id", value: this.props.id}), 
            React.createElement("fieldset", null, 
                React.createElement("label", null, "Title"), 
                React.createElement("input", {type: "text", name: "title", className: "form-group"})
            ), 
            React.createElement("fieldset", null, 
                React.createElement("label", null, "Dates"), 
                React.createElement("input", {type: "date", name: "start_date", className: "form-group"}), 
                React.createElement("input", {type: "date", name: "end_date", className: "form-group"})
            ), 
            React.createElement("fieldset", null, 
                React.createElement("label", null, "Location"), 
                React.createElement("input", {type: "text", name: "location", className: "form-group"})
            ), 
            React.createElement("button", {type: "submit", className: "btn btn-success"}, "Add Job")
        ), 
        React.createElement("hr", null), 
        React.createElement("div", {className: "search-results"}
        )
      )
    );
  }
});

var NewSchool = React.createClass({displayName: "NewSchool",
    render: function() {
    return (
      React.createElement("div", {className: "search-box row"}, 
        React.createElement("h1", null, "Add School"), 
        React.createElement("h4", null, this.props.name), 
        React.createElement("form", {action: "/educations/create", method: "POST"}, 
            React.createElement("input", {type: "hidden", name: "school_id", value: this.props.id}), 
            React.createElement("fieldset", null, 
                React.createElement("label", null, "Dates"), 
                React.createElement("input", {type: "date", name: "start_date", className: "form-group"}), 
                React.createElement("input", {type: "date", name: "end_date", className: "form-group"})
            ), 
            React.createElement("fieldset", null, 
                React.createElement("label", null, "Degree"), 
                React.createElement("input", {type: "text", name: "degree", className: "form-group"})
            ), 
            React.createElement("button", {type: "submit", className: "btn btn-success"}, "Add School")
        ), 
        React.createElement("hr", null), 
        React.createElement("div", {className: "search-results"}
        )
      )
    );
  }
});


var SchoolSearch = React.createClass({displayName: "SchoolSearch",
    render: function() {
    return (
      React.createElement("div", {className: "search-box row"}, 
        React.createElement("h1", null, "Search For A School"), 
        React.createElement("input", {type: "text", name: "school-name", className: "form-group"}), 
        React.createElement("button", {id: "school-search", className: "btn btn-success"}, "Search"), 
        React.createElement("hr", null), 
        React.createElement("div", {className: "search-results"}
        )
      )
    );
  }
});


var WorkSearch = React.createClass({displayName: "WorkSearch",
    render: function() {
    return (
      React.createElement("div", {className: "search-box"}, 
        React.createElement("div", {className: "step-one"}, 
            React.createElement("h1", null, "Search For A Company"), 
            React.createElement("input", {type: "text", name: "work-name", className: "form-group"}), 
            React.createElement("button", {id: "work-search", className: "btn btn-success"}, "Search"), 
            React.createElement("hr", null), 
            React.createElement("div", {className: "search-results"}
            )
        )
      )
    );
  }
});

function addJob() {
    $(".overlay").show();

    React.render(
        React.createElement(WorkSearch, null),
        document.getElementById('search-box')
    );
    bindButtons();

}

function addSchool() {
    $(".overlay").show();

    React.render(
        React.createElement(SchoolSearch, null),
        document.getElementById('search-box')
    );
    bindButtons();

}

function addSkill() {
    var skill = $('.skill-box').val()
    $('.skill-box').val('')
    $.post("/user/skills/add", params={skill:skill}, function(data) {
        React.render(
            React.createElement(Skills, {data: data.skills}),
            document.getElementById("skills")
            );
        bindDeleteSkill();
    });
}

function bindDeleteSkill() {
    $("[data-delete]").click(function(e) {
        var skill = $(this).data('delete');
        $.post("/user/skills/delete", params={skill:skill}, function(data) {
            React.render(
                React.createElement(Skills, {data: data.skills}),
                document.getElementById("skills")
                );
        });
    });
}

function closeProfile() {
    $(".overlay").fadeOut();
    $("#search-box").html("");
}


function bindButtons() {
    $("button#work-search").click(function(e) {
        e.preventDefault();
        var term = $("[name='work-name']").val().split(" ").join("+");


        $(".search-results").load("/elastic_search?type=companys&term=" + term, function() {
            $("[data-id").click(function() {
                var name = $(this).data("name");
                var id = $(this).data("id");
                React.render(
                    React.createElement(NewJob, {name: name, id: id}),
                    document.getElementById('search-box')
                )
            });
        });
    });

    $("button#school-search").click(function(e) {
        e.preventDefault();
        var term = $("[name='school-name']").val().split(" ").join("+");


        $(".search-results").load("/elastic_search?type=schools&term=" + term, function() {
            $("[data-id").click(function() {
                var name = $(this).data("name");
                var id = $(this).data("id");
                React.render(
                    React.createElement(NewSchool, {name: name, id: id}),
                    document.getElementById('search-box')
                )
            });
        });
    });
}

function bindSkill() {
    React.render(
        React.createElement(Skills, {data: window.sharedData.skills.skills}),
        document.getElementById("skills")
        );

    bindDeleteSkill();
}
bindSkill();
