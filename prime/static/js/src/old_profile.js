var userProfilePage = 1;
var page = 1;
var userPage = 1;
var colors = ["#B7D085", "#F9EBB5", "#D3102E", "#DCD6D5", "#39272A", "#27ACBE", "#3D9275", "#C7E1B8", "#BEC25D"];
var userIndustries = {}
var userLocations = {}
var user_school_connections = {}
var user_company_connections = {}

var UserProfileResults = React.createClass({
    getInitialState: function() {
        var data = [];
        var prospects = [];
        return {data: data,
                prospects:prospects};
    },
    componentDidMount: function() {
        userProfilePage++;
        var offset = 50 * (userProfilePage - 1);
        var limit = offset + 50;
        this.setState({prospects:this.props.data.splice(offset, limit)})
        setTimeout(this.loadInLinkedinScript, 1000);
        this.bindButtons();
    },
    loadInLinkedinScript: function() {
        IN.parse(document.body);
    },
    bindButtons: function() {
        var result = this;
        $(".add-prospect").click(function() {
            var id = $(this).data("id");
            $.post("/user/prospect/add/" + id, function(data) {
                $("[data-result='" + id + "']").fadeOut();
            });
        });

        $(".remove-prospect").click(function() {
            var id = $(this).data("id");
            $.post("/user/prospect/skip/" + id, function(data) {
                $("[data-result='" + id + "']").fadeOut();
            });
        });
        $("#more-prospects").click(function() {
            userProfilePage++;
            var offset = 50 * (userPage - 1);
            var limit = offset + 50;
            var data = this.props.data.splice(offset, limit);
            if (data.length > 0) {
                result.setState({prospects:data});
                result.bindButtons();
                $("html, body").animate({
                    scrollTop: $(".results").position().top
                }, 100);
            } else {
                bootbox.alert("There are no more Prospects");
                return false;
            }
        });
    },
    render: function() {
    var prospects = this.state.prospects.map(function(prospect) {

        return (
                <UserProspect data={prospect} />
            )
    });
    if (this.props.data.length < 1) {
        return (
          <div className="results prospect-profile-results">
              <div className="wrapper">
                  <div className='empty'>
                      <h2>There are no more prospects in your network</h2>
                      </div>
                  </div>
              <div className='clear'></div>
          </div>
        );
    } else {
        return (
          <div className="results prospect-profile-results">
            <div className="wrapper">
                <div className='stats'>
                  <div className='stat' id='u-one'>
                    <h5>Work Connections</h5>
                    <canvas id='one'></canvas>
                  </div>
                  <div className='stat' id='u-two'>
                    <h5>School Connections</h5>
                    <canvas id='two'></canvas>
                  </div>
                  <div className='stat' id='u-three'>
                    <h5>Industry Analysis</h5>
                    <canvas id='three'></canvas>
                  </div>
                  <div className='stat' id='u-four'>
                    <h5>Location Analysis</h5>
                    <canvas id='four'></canvas>
                  </div>
                </div>
                {prospects}
                <div className='clear'></div>
                <button className='btn btn-success' id='more-prospects'>More</button>
              </div>
          </div>
        );
    }
  }
});

var ProfileSalary = React.createClass({
    render: function() {
        return (
            <div className="salaryList">
            <h4>Estimated Salary Information</h4>
            <h3>{this.props.salary} *</h3>
            <p>* This information is based on industry averages.</p>
            </div>
            );
    }
});

var ProfileNews = React.createClass({
    render: function() {
    var newsNodes = this.props.data.map(function (news) {
        return (
            <div className="news">
                <h3>{news.Title}</h3>
                <h5><a href=''>{news.Url}</a></h5>
                <p>{news.Description}</p>
            </div>
            )
    });
    return (
        <div className="newsList">
            <h4>Relevant Links and News</h4>
            {newsNodes}
        </div>
        )
    }
});

var ProfileSchools = React.createClass({
    render: function() {
    var schoolNodes = this.props.data.map(function (school) {
        return (
            <div className="education">
                <h3>{school.school_name}</h3>
                <p>{school.degree} - {school.graduation}</p>
            </div>
            )
    });
    return (
      <div className="schoolList">
        <h4>Education History</h4>
        {schoolNodes}
      </div>
    );
  }
});

var ProfileJobs = React.createClass({
    render: function() {
    var jobNodes = this.props.data.map(function (job) {
        return (
            <div className="job">
                <h3>{job.company_name}</h3>
                <p>{job.title} - {job.location} - {job.dates}</p>
            </div>
            )
    });
    return (
      <div className="jobsList">
        <h4>Work History</h4>
        {jobNodes}
      </div>
    );
  }
});


var Profile = React.createClass({
    loadProfileFromServer: function() {
        $.ajax({
          url: this.props.url,
          dataType: 'json',
          success: function(data) {
            this.setState({data: data.prospect, client_lists:data.client_lists});
          }.bind(this),
          error: function(xhr, status, err) {
          }.bind(this)
        });
    },
    getInitialState: function() {
        return {data:{"jobs":[],"news": [], "schools": []}, client_lists:[]};
    },
    componentDidMount: function() {
        this.loadProfileFromServer();
        setTimeout(this.loadInLinkedinScript, 1000);
        this.bindButtons();
    },
    loadInLinkedinScript: function() {
        var $html = $('<script type="IN/MemberProfile" data-id="' + this.props.linkedin_url + '" data-related="false" data-format="inline"></script>')
        $(".leftTop").append($html);
        IN.parse(document.body);
    },
    bindButtons: function() {
        var result = this;
        $(".add-prospect").click(function() {
        });

        $(".remove-prospect").click(function() {
        });

        $("#show-user-profile").click(function() {
            $(".user-profile-tabs li").removeClass("active");
            $(this).parent().addClass("active");
            $(".prospect-profile-results").hide();
            $(".profile-content").fadeIn();

        });

        $("#show-user-prospects").click(function() {
            $(".user-profile-tabs li").removeClass("active");
            $(this).parent().addClass("active");
            $(".profile-content").hide();
            $(".prospect-profile-results").fadeIn();
        });
    },
    render: function() {
    var prospectId = this.state.data.id
    var results = this.state.data.results;
    var results = [];
    if (this.state.client_lists) {
        var clientLists = this.state.client_lists.map(function(cl) {
            return (
                <h4>Select: 
                <a href='javascript:addToList();' className='add-to-list' data-id={cl.id} data-prospect-id={prospectId}> {cl.name}</a>
                </h4>
                )
        });
    }
    return (
      <div className="profileBox">
        <div className="top">
          <div className="wrapper">
                <p>Investor Profile <a data-name='closeoverlay' href='#'><i className="fa fa-times-circle-o"></i></a></p>
            </div>
        </div>
        <div className='inner'>
            <div className="wrapper">
                <div className='leftTop'>
                </div>
                <div className='rightTop'>
                    <div className='group'>
                        <h1>{this.state.data.name}</h1>
                        <p>{this.state.data.location} | {this.state.data.industry}</p>
                    </div>
                    <div className='group'>
                        <h4 className="wealth">Wealthscore: <span className='inner'>{this.state.data.wealthscore}</span></h4>
                    </div>
                    <div className='clear'></div>
                    <a href='javascript:;'><button className='btn btn-success prospect-add'><i className='fa fa-plus'></i> Add To Prospect List</button></a>
                    <a data-skip={this.state.data.id} href='javascript:;'><button className='btn btn-danger'><i className='fa fa-chevron-circle-right'></i> Skip Prospect</button></a>
                    <div className='clear'></div>
                    <fieldset className='hidden-select'>
                        {clientLists}
                        <div>
                            <input type='text' className='form-group' id='new-list-name' placeholder='enter name' /><button id='create-new' data-prospect-id={prospectId} className='btn btn-success'>Create New +</button>
                        </div>
                    </fieldset>
                    <div className='clear'></div>
                </div>
                <hr />
                <ul className='tabs user-profile-tabs'>
                    <li className='active'><a href='javascript:;' id='show-user-profile' >Profile</a></li>
                    <li><a href='javascript:;' id='show-user-prospects'>Relevant Prospects</a></li>
                </ul>
                <ProfileJobs data={this.state.data.jobs} />
                <ProfileSchools data={this.state.data.schools} />
                <div className='clear'></div>
                <hr />
                <ProfileNews data={this.state.data.news} />
                <div className='clear'></div>
            </div>
        </div>
      </div>
    );
  }
});


$(function() {
    $("#person").show();
    $("html, body").animate({
        scrollTop: 0
    }, 100);

    url = "/ajax/prospect/" + id;
    React.render(
        <Profile url={url} linkedin_url={linkedin_url} />,
        document.getElementById('person')
    );
    IN.parse();
    $("[data-name='closeoverlay']").on("click", function() {
        closeProfile();
    });
    //bindProspectRequest();
    bindClientListButtons();
});

function closeProfile() {
    $(".overlay").fadeOut();
    $("#person").html("");
}

function bindClientListButtons() {
    $(function() {
        $(".chosen-select").chosen({width: "95%"}); 
        $("button.prospect-add").click(function(e) {
            $(".hidden-select").slideDown();
            addToList();
        });
    });
}

function addToList() {
    $(".add-to-list").click(function() {
        var id = $(this).data("id");
        var prospectId = $(this).data("prospect-id")
        $.post("/user/" + id + "/prospect/add/" + prospectId, function(data) {
            closeProfile();
            bootbox.alert("Client Processed!");
        })
    });

    $("#create-new").click(function() {
        var name = $("#new-list-name").val();
        var prospectId = $(this).data("prospect-id")
        params= {"name": name,
                "create_new": true}
        $.post("/user/1/prospect/add/" + prospectId, params, function(data) {
            closeProfile();
            bootbox.alert("Client Processed!");
        });
    });
}
