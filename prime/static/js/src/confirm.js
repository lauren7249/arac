var Skills = React.createClass({
    render: function() {
        var skills = this.props.data.map(function(skill) {
            return (
                <div className='skill'>
                    {skill}
                    <span data-delete={skill} className='delete'>X</span>
                </div>
                )
        });
        return (
            <div className='skills'>
                {skills}
            </div>
            )
    }
});

var NewJob = React.createClass({
    render: function() {
    return (
      <div className="search-box row">
        <h1>Add School</h1>
        <h4>{this.props.name}</h4>
        <form action='/jobs/create' method='POST'>
            <input type='hidden' name='company_id' value={this.props.id} />
            <fieldset>
                <label>Title</label>
                <input type='text' name='title' className='form-group' />
            </fieldset>
            <fieldset>
                <label>Dates</label>
                <input type='date' name='start_date' className='form-group' />
                <input type='date' name='end_date' className='form-group' />
            </fieldset>
            <fieldset>
                <label>Location</label>
                <input type='text' name='location' className='form-group' />
            </fieldset>
            <button type='submit' className='btn btn-success'>Add Job</button>
        </form>
        <hr />
        <div className='search-results'>
        </div>
      </div>
    );
  }
});

var NewSchool = React.createClass({
    render: function() {
    return (
      <div className="search-box row">
        <h1>Add School</h1>
        <h4>{this.props.name}</h4>
        <form action='/educations/create' method='POST'>
            <input type='hidden' name='school_id' value={this.props.id} />
            <fieldset>
                <label>Dates</label>
                <input type='date' name='start_date' className='form-group' />
                <input type='date' name='end_date' className='form-group' />
            </fieldset>
            <fieldset>
                <label>Degree</label>
                <input type='text' name='degree' className='form-group' />
            </fieldset>
            <button type='submit' className='btn btn-success'>Add School</button>
        </form>
        <hr />
        <div className='search-results'>
        </div>
      </div>
    );
  }
});


var SchoolSearch = React.createClass({
    render: function() {
    return (
      <div className="search-box row">
        <h1>Search For A School</h1>
        <input type='text' name='school-name' className='form-group' />
        <button id='school-search' className='btn btn-success'>Search</button>
        <hr />
        <div className='search-results'>
        </div>
      </div>
    );
  }
});


var WorkSearch = React.createClass({
    render: function() {
    return (
      <div className="search-box">
        <div className='step-one'>
            <h1>Search For A Company</h1>
            <input type='text' name='work-name' className='form-group' />
            <button id='work-search' className='btn btn-success'>Search</button>
            <hr />
            <div className='search-results'>
            </div>
        </div>
      </div>
    );
  }
});

function addJob() {
    $(".overlay").show();

    React.render(
        <WorkSearch/>,
        document.getElementById('search-box')
    );
    bindButtons();

}

function addSchool() {
    $(".overlay").show();

    React.render(
        <SchoolSearch/>,
        document.getElementById('search-box')
    );
    bindButtons();

}

function addSkill() {
    var skill = $('.skill-box').val()
    $('.skill-box').val('')
    $.post("/user/skills/add", params={skill:skill}, function(data) {
        React.render(
            <Skills data={data.skills} />,
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
                <Skills data={data.skills} />,
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
                    <NewJob name={name} id={id} />,
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
                    <NewSchool name={name} id={id} />,
                    document.getElementById('search-box')
                )
            });
        });
    });
}

function bindSkill() {
    React.render(
        <Skills data={window.sharedData.skills.skills} />,
        document.getElementById("skills")
        );

    bindDeleteSkill();
}
bindSkill();
