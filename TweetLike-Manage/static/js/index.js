// This will be the object that will contain the Vue attributes
// and be used to initialize it.
let app = {};

// Given an empty app object, initializes it filling its attributes,
// creates a Vue instance, and then initializes the Vue instance.
let init = (app) => {
    // This is the Vue data.
    app.data = {
        // Complete as you see fit.
        got_followed_status: false,
        users: [],
        followed_list: [],
        searchContent: "",

        results: [],
        query: "",
        textBox: "",
        meows: [],
    };

    app.enumerate = (a) => {
        // This adds an _idx field to each element of the array.
        let k = 0;
        a.map((e) => {
            e._idx = k++;
        });
        return a;
    };

    app.to_follow = function (user_id) {
        console.log("follow click!")
        axios
            .post(follow_url, {user_id: user_id})
            .then(function (r) {
                // update to get the updated list
                app.vue.followed_list.push(user_id);
                // update the followed list and followed status to true
                let user = null;
                for (let i = 0; i < app.vue.users.length; i++) {
                    if (app.vue.users[i].id === user_id) {
                        user = app.vue.users[i];
                        break;
                    }
                }
                if (user) {
                    user.got_followed_status = true;
                }
            })
    };

    app.unfollow = function (user_id) {
        console.log("unfollow click!")
        axios
            .post(unfollow_url, {user_id: user_id})
            .then(function (r) {
                // update status
                app.vue.users.forEach((user) => {
                    if (user.id === user_id) {
                        user.got_followed_status = false;
                    }
                });
            })
    };

    app.search = function () {
        //console.log("params:,", app.vue.searchContent);
        if (app.vue.searchContent.length >= 1) {
            axios.get(search_url, {params: {q: app.vue.searchContent}})
                .then(function (result) {
                    //console.log("vue.results:", result.data.results);
                    app.vue.users = result.data.results;
                });
        } else {
            app.loadData();
        }
    };

    app.publish = function () {
        if (app.vue.textBox.length >= 1) {
            console.log(app.vue.textBox);
            axios.post(publish_url, {content: app.vue.textBox})
                .then(function (response) {
                    console.log("POST request successful");
                    app.vue.meows.push(response.data);
                    console.log("Response data:", response.data.content);
                    app.loadData();
                    app.vue.textBox = '';

                })
                .catch(function (error) {
                    console.error("POST request error:", error);
                    throw error;
                });
        }
    };

    app.formatTimestamp = function (timestamp) {
        const now = new Date();
        const timestampDate = new Date(timestamp);
        const timeDiff = now.getTime() - timestampDate.getTime();
        const seconds = Math.floor(timeDiff / 1000);

        if (isNaN(timestampDate.getTime())) {
            return 'Invalid timestamp';
        } else if (seconds < 1) {
            return 'Just now';
        } else if (seconds < 60) {
            return seconds + ' seconds ago';
        } else if (seconds < 3600) {
            const minutes = Math.floor(seconds / 60);
            return minutes + ' minutes ago';
        } else if (seconds < 86400) {
            const hours = Math.floor(seconds / 3600);
            return hours + ' hours ago';
        } else {
            const days = Math.floor(seconds / 86400);
            return days + ' days ago';
        }
    }

    app.reload = function () {
        app.vue.searchContent = '';
        app.vue.search();
        console.log("reload fcn loaded");
    };

    app.loadData = function () {
        axios.get(get_users_url).then(function (r) {
            app.vue.users = [];
            if (r.data.followed_list) {
                app.vue.followed_list = r.data.followed_list;
            } else {
                app.vue.followed_list = [];
            }

            var users = r.data.users;
            for (var i = 0; i < users.length; i++) {
                var user = users[i];
                if (!user.got_followed_status) {
                    user.got_followed_status = false;
                }
                app.vue.users.push(user);
            }
        });
        axios.get(get_meows_url).then(function (r) {
            app.vue.meows = r.data.meows;
        });
    };

    // This contains all the methods.
    app.methods = {
        // Complete as you see fit.
        //start_insert: app.start_insert,
        to_follow: app.to_follow,
        unfollow: app.unfollow,
        search: app.search,
        reload: app.reload,
        publish: app.publish,
        formatTimestamp: app.formatTimestamp,
    };

    // This creates the Vue instance.
    app.vue = new Vue({
        el: "#vue-target",
        data: app.data,
        methods: app.methods
    });

    app.init = () => {
        app.loadData()
    };

    // Call to the initializer.
    app.init();
};

// This takes the (empty) app object, and initializes it,
// putting all the code i
init(app);
