var gulp = require('gulp'),
    notify = require('gulp-notify'),
    concat = require('gulp-concat');


gulp.task('default', function() {
    gulp.start('concatStyle');
    gulp.start('concatScripts');
    gulp.start('concatScriptsByIe');
});

gulp.task('concatStyle', function() {
  return gulp.src([
          'node_modules/bootstrap/dist/css/bootstrap.min.css',
          'node_modules/font-awesome/css/font-awesome.min.css',
          'node_modules/ionicons/dist/css/ionicons.min.css',
          'node_modules/select2/dist/css/select2.min.css',
          'node_modules/highlight.js/styles/default.css',
          'static/css/AdminLTE.min.css',
          'static/plugins/iCheck/square/blue.css',
          'node_modules/diff2html/dist/diff2html.min.css',
    ])
    .pipe(concat('common.css'))
    .pipe(gulp.dest('static/css/'))
    .pipe(notify({ message: 'Style task complete' }));
});

gulp.task('concatScripts', function() {
  return gulp.src([
          'node_modules/jquery/dist/jquery.min.js',
          'node_modules/bootstrap/dist/js/bootstrap.min.js',
          'node_modules/select2/dist/js/select2.min.js',
          'static/plugins/iCheck/icheck.min.js',
          'node_modules/clipboard/dist/clipboard.min.js',
          'node_modules/diff2html/dist/diff2html.min.js',
          'node_modules/diff2html/dist/diff2html-ui.min.js',
          'node_modules/js-base64/base64.min.js',
          'node_modules/highlight.js/lib/highlight.js',
    ])
    .pipe(concat('common.js'))
    .pipe(gulp.dest('static/js/'))
    .pipe(notify({ message: 'Scripts task complete' }));
});

gulp.task('concatScriptsByIe', function() {
  return gulp.src([
          'node_modules/html5shiv/dist/html5shiv.min.js',
          'static/js/respond.min.js'
    ])
    .pipe(concat('ie.js'))
    .pipe(gulp.dest('static/js/'))
    .pipe(notify({ message: 'Scripts task complete' }));
});
