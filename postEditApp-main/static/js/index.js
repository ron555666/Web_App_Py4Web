
let app = {};

// Given an empty app object, initializes it filling its attributes,
// creates a Vue instance, and then initializes the Vue instance.
let init = (app) => {
  app.data = {
    search: '',
    users: [],
    following: {},
    add_mode: false,
    add_first_name: "",
    add_title: "",
    add_caption: "",
    add_thumbnail: null,
    rows: [],
    colors: ['pastel-red', 'pastel-blue', 'pastel-yellow', 'no-color'],
    selectedColor: 'no-color',
    comments: {},
    mark: false,
  };

  app.enumerate = (a) => {
    let k = 0;
    a.map((e) => {
      e._idx = k++;
    });
    return a;
  };

  app.methods = {
markContact: function(rowIdx) {
  let contact = this.rows[rowIdx];
  console.log(contact);
  contact.mark = !contact.mark;

  axios.post(mark_contact_url, {
    contact_id: contact.id,
    mark: contact.mark,
  }).then(function(response) {
    console.log("Contact marked:", contact.id);
  }).catch(function(error) {
    console.error("Failed to mark contact:", error);
  });
  console.log(contact.mark);
},


    set_color: function(event) {
      // Set the selected color
      this.selected_color = event.target.value;

      // Send the selected color to server
      axios.post(set_add_status_url, {
        selected_color: this.selected_color,
      });
    },

add_contact: function () {
  axios.post(add_contact_url, {
    title: app.vue.add_title,
    caption: app.vue.add_caption,
    color: app.vue.selectedColor,
    thumbnail: app.vue.add_thumbnail,
    mark: app.vue.mark,
  }).then(function (response) {
    let new_row = {
      id: response.data.id,
      first_name: response.data.first_name,  // Use the first name from the response
      title: app.vue.add_title,
      caption: app.vue.add_caption,
      color: app.vue.selectedColor,
      thumbnail: app.vue.add_thumbnail,
      mark: app.vue.mark,
      _state: { title: "clean", caption: "clean" },
      _idx: 0,
    };
    app.vue.rows.forEach((row) => {
      row._idx += 1;
    });
    app.vue.rows.unshift(new_row);
  });
  setTimeout(function () {
    app.vue.add_title = "";
    app.vue.add_caption = "";
    app.vue.add_thumbnail = null;
    app.vue.mark = false;
  }, 100);
  app.vue.add_mode = false;
},

    reset_form: function () {
      app.vue.add_title = "";
      app.vue.add_caption = "";
    },

    delete_contact: function (row_idx) {
      let id = app.vue.rows[row_idx].id;
      axios.get(delete_contact_url, { params: { id: id } }).then(function (response) {
        for (let i = 0; i < app.vue.rows.length; i++) {
          if (app.vue.rows[i].id === id) {
            app.vue.rows.splice(i, 1);
            app.enumerate(app.vue.rows);
            break;
          }
        }
      });
    },

    set_add_status: function (new_status) {
      app.vue.add_mode = new_status;
      axios.post(set_add_status_url, { add_mode: new_status }).then(function (response) {
        app.vue.selectedColor = response.data.selectedColor;
      });
    },

    start_edit: function (row_idx, fn) {
      let row = app.vue.rows[row_idx];
      app.vue.rows[row_idx]._state[fn] = "edit";
    },

    stop_edit: function (row_idx, fn) {
      let row = app.vue.rows[row_idx];
      if (row._state[fn] === "edit") {
        row._state[fn] = "pending";
        axios.post(edit_contact_url, {
          id: row.id,
          field: fn,
          value: row[fn], // row.title
        }).then(function (result) {
          row._state[fn] = "clean";
        });
      }
    },

    temp_upload: function (event) {
      let input = event.target;
      let file = input.files[0];

      if (file) {
        let reader = new FileReader();
        reader.addEventListener("load", function () {
          // 将文件路径保存到 add_thumbnail
          app.vue.add_thumbnail = reader.result;
        });
        reader.readAsDataURL(file);
      }
    },

    upload_file: function (event, row_idx) {
      let input = event.target;
      let file = input.files[0];
      let row = app.vue.rows[row_idx];
      if (file) {
        let reader = new FileReader();
        reader.addEventListener("load", function () {
          axios.post(upload_thumbnail_url, {
            contact_id: row.id,
            thumbnail: reader.result,
          }).then(function () {
            row.thumbnail = reader.result;
          });
        });
        reader.readAsDataURL(file);
      }
    },
  };

  app.decorate = (a) => {
    a.map((e) => {
      e._state = { title: "clean", caption: "clean" };
    });
    return a;
  };

  app.vue = new Vue({
    el: "#vue-target",
    data: app.data,
    methods: app.methods,
  });

app.init = () => {
  axios.get(load_contacts_url).then(function (response) {
    app.vue.rows = app.decorate(app.enumerate(response.data.rows));
    app.vue.rows = app.vue.rows.map(row => ({ ...row, color: row.color || 'no-color' })); // ensure that each row has a color attribute
    app.vue.rows.reverse();
    app.enumerate(app.vue.rows);
  });
};


  app.init();
};

init(app); // This will be the object that will contain the Vue attributes
// and be used to initialize it.

