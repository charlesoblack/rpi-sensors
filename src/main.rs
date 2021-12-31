use gpio::{GpioIn, GpioOut};
use std::{thread, time};

fn main() {
    let mut data_pin = gpio::sysfs::SysFsGpioOutput::open(36).unwrap();

    data_pin.set_value(false).expect("could not set init value false");
    thread::sleep(time::Duration::from_millis(20));
    data_pin.set_value(true).expect("could not set init value true");
    thread::sleep(time::Duration::from_micros(30));

    let mut data_pin = gpio::sysfs::SysFsGpioInput::open(36).unwrap();

    loop {
        println!("GPIO 36: {:?}", data_pin.read_value().unwrap());
        thread::sleep(time::Duration::from_micros(1));
    }
}
