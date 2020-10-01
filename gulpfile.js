var gulp = require('gulp');
var sass = require('gulp-sass');
var autoprefixer = require('autoprefixer');
var concat = require('gulp-concat');
var postcss = require('gulp-postcss');
var sourcemaps = require('gulp-sourcemaps');
var browserSync = require('browser-sync').create();
var reload = browserSync.reload;
var useref = require("gulp-useref");
var gulpIf = require('gulp-if');
var uglify = require('gulp-uglify-es').default;
var cssnano = require('gulp-cssnano');
var htmlmin = require('gulp-htmlmin');
var rename = require('gulp-rename');
var imagemin = require('gulp-imagemin');
var del = require('del');
var runSequence = require('run-sequence');
var wait = require('gulp-wait');
var spawn = require('child_process').spawn;
// Run the Django development server
gulp.task('django', function() {
    const spawn = require('child_process').spawn;
    return spawn('python', ['manage.py', 'runserver'])
        .stderr.on('data', (data) => {
        console.log(`${data}`);
    });
});

gulp.task('sass', function(){
  gulp.src('bat/static/app/sass/**/*.scss')
  .pipe(wait(700))
  .pipe(sass())
  .pipe(gulp.dest("bat/static/app/css"))
  .pipe(cssnano({zindex: false}))
  .pipe(rename({ suffix: '.min' }))
  .pipe(gulp.dest("bat/static/app/css"));
});

// Initiate browsersync and point it at localhost:8000
gulp.task('browsersync', function() {
    browserSync.init({
        notify: true,
        proxy: "localhost:8000",
    });
});

// Tell gulp to executed 'styles' when sass files change, and execute
// a browser reload when any file changes.
gulp.task("watch", gulp.parallel("browsersync", "sass", function() {
  gulp.watch("bat/static/app/sass/**/*.scss", ["sass"]);
  gulp.watch(['bat/static/app/**/*.{scss,css,html,py,js}'], reload);
}));

gulp.task("minifyjs", function() {
  return gulp.src('bat/static/app/js/**/*')
  .pipe(gulpIf('*.js', uglify()))
});

gulp.task("minifycss", function() {
  return gulp.src('bat/static/app/css/**/*')
  .pipe(gulpIf('*.css', cssnano({zindex: false})))
});

gulp.task('images', function(){
  return gulp.src('bat/static/app/images/*.+(png|jpg|gif|svg)')
  .pipe(imagemin())

});

gulp.task('font', function() {
  return gulp.src('bat/static/app/fonts/**/*')
});

gulp.task('clean:dist', function() {
  return del.sync('static/dist');
})


// 'gulp' calls django, browsersync, and watch tasks
gulp.task('default', gulp.parallel('django','sass','browsersync'));

gulp.task('build', function (callback) {
  runSequence('clean:dist', 'sass',
    ["minifyjs", "minifycss", "images", 'font'],
    callback
  )
})
