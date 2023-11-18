function preload(){
    img = loadImage('/static/img/sumida1.png');    //画像の読み込み
  }

function setup() {
    canvas = createCanvas(windowWidth,windowHeight);//2Dの場合は引数にWEBGLは要らない
}
function draw() {
    background(33,96,144);
    img = draw_noise(img);
	img = draw_color_glitch(img, 1);
    img = draw_shift_glitch(img, 3);

    image(img, 0, 0);
}

function draw_noise(img){
    background(0);
    image(img, 0, 0);

    let noise_size = 5;

    push();
    strokeWeight(0);
      for(let i=0;i<img.width;i+=noise_size){
          for(let j=0;j<img.height;j+=noise_size){
              if(random()<0.5){
                  fill(random([0, 255]), 100*noise(i, j));
                  rect(i, j, noise_size);
              }
          }
      }
    pop();

      let img_noise = get();
      clear();

    return img_noise;
  }

function draw_color_glitch(img, shift_size){
    background(0);

    let left_color = color(255, 0, 0);
    let right_color = color(0, 255, 255);

    push();
    blendMode(ADD);

    tint(left_color);
    image(img, -shift_size, 0);

    tint(right_color);
    image(img, shift_size, 0);
    pop();

      let img_glitch = get();
      clear();

    return img_glitch;
  }

  function draw_shift_glitch(img, shift_size){
    background(0);
      image(img, 0, 0);

      for(let i=0;i<100;i++){
          let sx = random(img.width*0.5);
          let sy = random(img.height*0.05);
          let x = random(img.width - sx*0.5);
          let y = random(img.height - sy*0.5);
          let ix = x + random(-1, 1)*shift_size;
          let iy = y ;
          image(img, ix, iy, sx, sy, x, y, sx, sy);
      }

      let img_glitch = get();
      clear();

    return img_glitch;
  }