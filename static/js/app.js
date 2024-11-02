// static/js/app.js

// Generate a unique ID for the tab if it doesn't exist
if (!localStorage.tabId) {
    localStorage.tabId = Math.random().toString(36).substr(2, 9);
}

// Function to store session data
function storeSessionData(sessionData) {
    sessionStorage.setItem(localStorage.tabId, JSON.stringify(sessionData));
}

// Function to retrieve session data
function getSessionData() {
    return JSON.parse(sessionStorage.getItem(localStorage.tabId));
}

// Function to store the JWT token
function storeAuthToken(token) {
    sessionStorage.setItem('authToken', token);
}

// Function to get the JWT token
function getAuthToken() {
    return sessionStorage.getItem('authToken');
}

// Example usage: store token on login
function onLoginSuccess(jwtToken) {
    storeAuthToken(jwtToken);
}

// Example usage: send authenticated request
function sendAuthenticatedRequest(url, options = {}) {
    const token = getAuthToken();
    if (!options.headers) {
        options.headers = {};
    }
    options.headers['Authorization'] = `Bearer ${token}`;
    return fetch(url, options);
}

// Logout functionality
function logout() {
    // Clear sessionStorage upon logout
    sessionStorage.clear();
    // Redirect to logout route or handle as needed
    fetch('/logout', {
        method: 'POST'
    })
    .then(response => {
        if (response.ok) {
            // Redirect to login page or desired destination
            window.location.href = '/index';
        } else {
            console.error('Logout failed.');
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}
//profile picture
$(document).ready(function() {
    $('#file-input').change(function() {
        const file = this.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function(e) {
                $('#profile-pic').attr('src', e.target.result).show();
            }
            reader.readAsDataURL(file);
            $('#file-name').text(file.name);
        } else {
            $('#file-name').text('No file chosen');
            $('#profile-pic').hide();
        }
    });
});
// Document ready function
$(document).ready(function() {
    $('#profile-toggle').on('click', function(e) {
        e.preventDefault();
        $(this).next('.dropdown-content').toggle();
    });

    $('#logout-link').on('click', function(e) {
        e.preventDefault();
        logout();
    });

    // Toggle menu for mobile
    $('.menu-toggle').on('click', function() {
        $('nav').addClass('show');
    });

    // Close menu
    $('.close-toggle').on('click', function() {
        $('nav').removeClass('show');
    });

    // Close dropdown if clicked outside
    $(document).on('click', function(event) {
        if (!$(event.target).closest('#profile-toggle').length) {
            $('.dropdown-content').hide();
        }
    });

    //Search box
    $('#search-box').on('input', function() {
        let query = $(this).val();
        if (query.length > 1) {
            $.ajax({
                url: '/search',
                method: 'GET',
                data: { query: query },
                success: function(data) {
                    $('#suggestions').empty();
                    data.forEach(function(item) {
                        $('#suggestions').append('<div class="suggestion-item">' + item.Title + '</div>');
                    });
                }
            });
        } else {
            $('#suggestions').empty();
        }
    });
    
    //Search button
    $('#search-btn').on('click', function() {
        let query = $('#search-box').val();
        if (query.length > 1) {
            window.location.href = '/project/' + encodeURIComponent(query);
        }
    });

    $(document).on('click', '.suggestion-item', function() {
        let title = $(this).text();
        $('#search-box').val(title);
        $('#suggestions').empty();
    });

});

    document.addEventListener('DOMContentLoaded', (event) => {
        const resultsPerPageDropdown = document.getElementById('results_per_page');
        
        resultsPerPageDropdown.addEventListener('change', function() {
            const selectedValue = this.value;
            const urlParams = new URLSearchParams(window.location.search);

            // Update the 'results_per_page' parameter
            if (selectedValue) {
                urlParams.set('results_per_page', selectedValue);
            } else {
                urlParams.delete('results_per_page');
            }

            // Reset to the first page
            urlParams.set('page', 1);

            // Redirect to the updated URL
            window.location.search = urlParams.toString();
        });
    });


// Function to save a project
function saveProject(projectId) {
    $.ajax({
        type: 'POST',
        url: '/save_project',
        contentType: 'application/json',
        data: JSON.stringify({ project_id: projectId }),
        success: function(response) {
            console.log('Save project response:', response); // Log response for debugging

            if (response.saved) {
                if (response.already_saved) {
                    console.log('Project was already saved');
                    $('#save-btn-' + projectId)
                        .removeClass('blue')
                        .addClass('green')
                        .text('Saved');
                } else {
                    console.log('Project saved successfully');
                    $('#save-btn-' + projectId)
                        .removeClass('blue')
                        .addClass('green')
                        .text('Saved');
                }
            } else {
                console.log('Failed to save project');
                // Optionally handle failure case
            }
        },
        error: function(xhr, textStatus, errorThrown) {
            console.error('Error saving project:', textStatus, errorThrown);
        }
    });
}

//Function to delete saved project from user library
function deleteProject(entryId) {
    $.ajax({
        type: 'POST',
        url: '/delete_project',
        contentType: 'application/json',
        data: JSON.stringify({ entry_id: entryId }),
        success: function() {
            $('#project_' + entryId).remove();
        },
        error: function(xhr, textStatus, errorThrown) {
            console.error('Error deleting project:', textStatus);
        }
    });
}

document.addEventListener("DOMContentLoaded", function() {
    const contentWrappers = document.querySelectorAll(".content-wrapper");
    contentWrappers.forEach(wrapper => {
        wrapper.classList.add("collapsed");
        wrapper.style.maxHeight = "80px"; // Set initial max height for collapsed state
    });
});

function toggleContent(button) {
    const contentWrapper = button.previousElementSibling;

    if (contentWrapper.classList.contains('collapsed')) {
        contentWrapper.style.maxHeight = contentWrapper.scrollHeight + 'px';
        button.innerText = 'Read Less';
        contentWrapper.classList.remove('collapsed');
    } else {
        contentWrapper.style.maxHeight = '80px';
        button.innerText = 'Read More';
        contentWrapper.classList.add('collapsed');
    }
}


document.getElementById('loginForm').addEventListener('submit', function(event) {
    event.preventDefault();
    
    let formData = new FormData(this);
    fetch('/login', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Store username in localStorage upon successful login
            localStorage.setItem('loggedInUser', data.username);
            // Redirect to homepage or desired page
            window.location.href = '/home';  // Example redirection after login
        } else {
            alert('Login failed. Please try again.');
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
});

function openTab(tabId) {
    // Hide all tab content
    const tabContents = document.querySelectorAll('.tab-content');
    tabContents.forEach(content => {
        content.classList.remove('active');
    });

    // Deactivate all tab buttons
    const tabButtons = document.querySelectorAll('.tab-button');
    tabButtons.forEach(button => {
        button.classList.remove('active');
    });

    // Show the selected tab content
    document.getElementById(tabId).classList.add('active');

    // Activate the selected tab button
    const activeButton = document.querySelector(`.tab-button[onclick="openTab('${tabId}')"]`);
    if (activeButton) {
        activeButton.classList.add('active');
    }
}

// Optional: Show the first tab by default
document.addEventListener('DOMContentLoaded', () => {
    openTab('pdf');
});

//developers
/* Toggle between adding and removing the "active" and "show" classes when the user clicks on one of the "Section" buttons. The "active" class is used to add a background color to the current button when its belonging panel is open. The "show" class is used to open the specific accordion panel */
var acc = document.getElementsByClassName("accordion");
var i;

for (i = 0; i < acc.length; i++) {
    acc[i].onclick = function(){
        this.classList.toggle("active");
        this.nextElementSibling.classList.toggle("show");
    }
    
}



   